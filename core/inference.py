"""
Real-time inference pipeline for SafeSight AI.
Orchestrates detection, tracking, violation evaluation, and logging.
"""

import cv2
import time
import threading
import numpy as np
from typing import Optional, Dict, Any

try:
    from ultralytics import YOLO
    import torch
    _YOLO_AVAILABLE = True
except ImportError:
    YOLO = None  # type: ignore[assignment,misc]
    torch = None  # type: ignore[assignment]
    _YOLO_AVAILABLE = False

from config.settings import (
    MODEL_PATH, IMG_SIZE, CONF_THRESHOLD, 
    DEVICE, TARGET_FPS, PPE_MEMORY_WINDOW_SECONDS
)
from core.detector import DetectionParser
from core.tracker import CentroidTracker
from core.violation_logic import ViolationEngine
from services.logger import ViolationLogger
from services.file_logger import FileLogService


class InferencePipeline:
    """
    Real-time inference pipeline for PPE violation detection.
    
    Pipeline flow per frame:
    Frame → YOLO detect → DetectionParser.parse() → Tracker.update() 
    → ViolationEngine.evaluate() → Logger.enqueue() → Render frame
    """
    
    def __init__(self, 
                 model_path: str = MODEL_PATH,
                 img_size: int = IMG_SIZE,
                 conf_threshold: float = CONF_THRESHOLD,
                 shared_model: Optional[YOLO] = None,
                 stream_id: str = "main"):
        """
        Initialize inference pipeline.
        
        Args:
            model_path: Path to YOLO model file
            img_size: Input image size for model
            conf_threshold: Confidence threshold for detections
            shared_model: Optional pre-loaded YOLO model to share across pipelines
            stream_id: Unique identifier for this stream (used in window titles & logs)
        """
        self.stream_id = stream_id
        
        print(f"\n{'='*50}")
        print(f"Initializing Pipeline [{stream_id}]")
        print("="*50)
        
        # Load or reuse YOLO model
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        if not _YOLO_AVAILABLE:
            raise RuntimeError(
                "ultralytics / torch not installed. "
                "Set USE_REMOTE_INFERENCE=true to use RemoteInferencePipeline instead."
            )

        if shared_model is not None:
            self.model = shared_model
            print(f"🔗 Reusing shared model on {self.device}")
        else:
            print(f"📦 Loading model from: {model_path}")
            print(f"🔧 Device: {self.device}")
            self.model = YOLO(model_path)
        
        # Thread lock for model inference (YOLO is not thread-safe)
        self._model_lock: Optional[threading.Lock] = None
        
        self.img_size = img_size
        self.conf_threshold = conf_threshold
        
        # Initialize pipeline components
        self.detector = DetectionParser(conf_threshold=conf_threshold)
        self.tracker = CentroidTracker()
        self.violation_engine = ViolationEngine()
        self.logger = ViolationLogger()
        self.file_logger: Optional[FileLogService] = None
        
        # Counters for session summary
        self._critical_count = 0
        self._warning_count = 0
        self._normal_count = 0
        
        # Latest annotated frame for MJPEG streaming (thread-safe)
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        
        # Performance tracking
        self.frame_count = 0
        self.fps = 0
        self.start_time = time.time()
        
        print(f"⏱️  PPE Memory Window: {PPE_MEMORY_WINDOW_SECONDS}s")
        print(f"✅ Pipeline [{stream_id}] initialized\n")
    
    def set_model_lock(self, lock: threading.Lock):
        """Set a shared lock for thread-safe model inference."""
        self._model_lock = lock
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return the latest annotated frame (thread-safe). Returns None if no frame yet."""
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None
    
    def start_logger(self):
        """Start the violation logger background thread."""
        self.logger.start()
    
    def stop_logger(self):
        """Stop the violation logger background thread."""
        self.logger.stop()
    
    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a single frame through the complete pipeline.
        
        Args:
            frame: Input video frame as numpy array
            
        Returns:
            Tuple of (annotated_frame, stats_dict)
        """
        frame_start = time.time()
        
        # 1. YOLO Detection (thread-safe with lock)
        if self._model_lock:
            with self._model_lock:
                results = self.model(
                    frame,
                    imgsz=self.img_size,
                    conf=self.conf_threshold,
                    device=self.device,
                    verbose=False
                )
        else:
            results = self.model(
                frame,
                imgsz=self.img_size,
                conf=self.conf_threshold,
                device=self.device,
                verbose=False
            )
        
        # 2. Parse Detections
        detections = self.detector.parse(results)
        persons = self.detector.get_persons(detections)
        ppe_detections = self.detector.get_ppe(detections)
        
        # 3. Track Persons
        tracked_persons = self.tracker.update(persons)
        
        # 4. Evaluate Violations (with frame height for visibility heuristics)
        frame_height = frame.shape[0]
        violations = self.violation_engine.evaluate(tracked_persons, ppe_detections, frame_height)
        
        # 5. Log Violations (non-blocking) — all violations go to DB
        for violation in violations:
            is_critical = violation.get("helmet_violation") and violation.get("vest_violation")
            has_violations = bool(violation.get("violations"))

            if is_critical:
                # CRITICAL: save evidence image + DB + alert
                self.logger.enqueue(violation, frame, save_image=True)
                if self.file_logger:
                    self.file_logger.log_critical(
                        violation["person_id"],
                        violation.get("violations", [])
                    )
                    self._critical_count += 1
            elif has_violations:
                # WARNING: DB + alert (no image to save disk)
                self.logger.enqueue(violation, frame, save_image=False)
                if self.file_logger:
                    self.file_logger.log_warning(
                        violation["person_id"],
                        violation.get("violations", [])
                    )
                    self._warning_count += 1

        # File log — NORMAL for persons with zero violations
        if self.file_logger:
            violating_ids = {v["person_id"] for v in violations}
            for person in tracked_persons:
                if person["person_id"] not in violating_ids:
                    self.file_logger.log_normal(person["person_id"])
                    self._normal_count += 1
        
        # 6. Render Annotated Frame
        annotated_frame = self._render_frame(frame, tracked_persons, violations, detections)
        
        # Update performance stats
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        self.fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        frame_time = time.time() - frame_start
        
        stats = {
            "fps": round(self.fps, 1),
            "frame_time": round(frame_time * 1000, 1),  # ms
            "detections": len(detections),
            "persons": len(tracked_persons),
            "violations": len(violations),
            "queue_size": self.logger.get_queue_size()
        }
        
        return annotated_frame, stats
    
    def _render_frame(self, frame: np.ndarray, 
                     tracked_persons: list,
                     violations: list,
                     all_detections: list) -> np.ndarray:
        """
        Render bounding boxes and information on frame.
        
        Args:
            frame: Input frame
            tracked_persons: List of tracked person objects
            violations: List of violation objects
            all_detections: All detections including PPE
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        # Create violations lookup
        violation_map = {v["person_id"]: v for v in violations}
        
        # Draw tracked persons
        for person in tracked_persons:
            person_id = person["person_id"]
            bbox = person["bbox"]
            x1, y1, x2, y2 = map(int, bbox)
            
            # Check if this person has violations
            if person_id in violation_map:
                violation = violation_map[person_id]
                severity = violation.get("severity", "WARNING")
                color = (0, 0, 255) if severity == "CRITICAL" else (0, 165, 255)  # Red / Orange
                label = f"Person {person_id} - {severity}"
                violations_text = ", ".join(violation["violations"])
                
                # Draw bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                # Draw label background
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated, (x1, y1 - 20), (x1 + label_size[0], y1), color, -1)
                cv2.putText(annotated, label, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Draw violations text
                cv2.putText(annotated, f"Missing: {violations_text}", (x1, y2 + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            else:
                color = (0, 255, 0)  # Green for compliant
                label = f"Person {person_id} - OK"
                
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated, label, (x1, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Draw PPE detections (smaller boxes)
        for detection in all_detections:
            if detection["class"] != "Person":
                bbox = detection["bbox"]
                x1, y1, x2, y2 = map(int, bbox)
                color = (255, 255, 0)  # Yellow for PPE
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1)
                cv2.putText(annotated, detection["class"], (x1, y1 - 3),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        # Draw stats overlay
        self._draw_stats_overlay(annotated)
        
        return annotated
    
    def _draw_stats_overlay(self, frame: np.ndarray):
        """Draw performance stats on frame."""
        h, w = frame.shape[:2]
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (250, 130), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Stats text
        stats_text = [
            f"[{self.stream_id}]",
            f"FPS: {self.fps:.1f}",
            f"Frames: {self.frame_count}",
            f"Tracked: {self.tracker.get_active_count()}",
            f"Queue: {self.logger.get_queue_size()}"
        ]
        
        y_offset = 30
        for text in stats_text:
            cv2.putText(frame, text, (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            y_offset += 20
    
    def run_video(self, source, display: bool = True):
        """
        Run inference on video source.
        
        Args:
            source: Video source (0 for webcam, video file path, or RTSP URL)
            display: Whether to display video window
        """
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print(f"❌ Error opening video source: {source}")
            return
        
        print(f"📹 [{self.stream_id}] Starting inference on: {source}")
        print(f"⏱️  PPE Memory Window: {PPE_MEMORY_WINDOW_SECONDS}s")
        print("Press 'q' to quit\n")
        
        # Init file logger for this video session
        self.file_logger = FileLogService(video_source=source)
        
        # Start logger
        self.start_logger()
        
        window_title = f"SafeSight AI - {self.stream_id}"
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"📹 [{self.stream_id}] End of video stream")
                    break
                
                # Process frame
                annotated_frame, stats = self.process_frame(frame)
                
                # Store latest frame for MJPEG streaming
                with self._frame_lock:
                    self._latest_frame = annotated_frame
                
                # Display
                if display:
                    cv2.imshow(window_title, annotated_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print(f"\n⏹️  [{self.stream_id}] User requested stop")
                        break
                
                # Print stats periodically
                if self.frame_count % 30 == 0:
                    print(f"[{self.stream_id}] FPS: {stats['fps']} | Persons: {stats['persons']} | "
                          f"Violations: {stats['violations']} | Queue: {stats['queue_size']}")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.stop_logger()
            
            # Write session summary and close file logs
            if self.file_logger:
                self.file_logger.log_summary(
                    total_frames=self.frame_count,
                    avg_fps=self.fps,
                    critical_count=self._critical_count,
                    warning_count=self._warning_count,
                    normal_count=self._normal_count
                )
                self.file_logger.close()
            
            # Clear frame buffer
            with self._frame_lock:
                self._latest_frame = None
            
            print(f"\n✅ [{self.stream_id}] Inference complete. Processed {self.frame_count} frames")
            print(f"📊 [{self.stream_id}] Average FPS: {self.fps:.1f}")
            print(f"📄 [{self.stream_id}] Critical: {self._critical_count} | Warning: {self._warning_count} | Normal: {self._normal_count}")

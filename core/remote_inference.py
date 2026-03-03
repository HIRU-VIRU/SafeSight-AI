"""
Remote Inference Pipeline for SafeSight AI.

Drop-in replacement for InferencePipeline that offloads YOLO detection
to a HuggingFace Space instead of running the model locally.

Architecture:
  Render (this file)            HuggingFace Space
  ─────────────────────         ─────────────────────
  frame → JPEG encode  ──POST──> /infer
                        <──JSON── detections[]
  CentroidTracker.update()
  ViolationEngine.evaluate()
  Logger.enqueue()
  cv2 render / annotate

No torch / ultralytics required on Render.
"""

import base64
import threading
import time
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import requests

from config.settings import (
    CONF_THRESHOLD,
    IMG_SIZE,
    PPE_MEMORY_WINDOW_SECONDS,
    HF_INFERENCE_URL,
)
from core.tracker import CentroidTracker
from core.violation_logic import ViolationEngine
from services.logger import ViolationLogger
from services.file_logger import FileLogService


class RemoteInferencePipeline:
    """
    Inference pipeline that sends frames to a remote HuggingFace Space
    for YOLO detection and handles tracking / violation logic locally.

    Interface is identical to InferencePipeline so the rest of the codebase
    (dashboard_api.py, app.py) requires zero changes – just swap the class.
    """

    def __init__(
        self,
        infer_url: str = HF_INFERENCE_URL,
        conf_threshold: float = CONF_THRESHOLD,
        img_size: int = IMG_SIZE,
        stream_id: str = "main",
        request_timeout: int = 10,
    ):
        """
        Args:
            infer_url       : Full URL of the HF Space /infer endpoint.
            conf_threshold  : Confidence threshold forwarded to YOLO.
            img_size        : YOLO input size forwarded to HF Space.
            stream_id       : Unique label for this stream.
            request_timeout : HTTP timeout in seconds per frame request.
        """
        self.stream_id = stream_id
        self.infer_url = infer_url.rstrip("/") + "/infer"
        self.conf_threshold = conf_threshold
        self.img_size = img_size
        self.request_timeout = request_timeout

        print(f"\n{'='*50}")
        print(f"Initializing RemotePipeline [{stream_id}]")
        print(f"  HF Endpoint : {self.infer_url}")
        print(f"  Conf        : {conf_threshold}")
        print(f"  ImgSize     : {img_size}")
        print("=" * 50)

        # Pipeline components (run locally on Render — no torch needed)
        self.tracker = CentroidTracker()
        self.violation_engine = ViolationEngine()
        self.logger = ViolationLogger()
        self.file_logger: Optional[FileLogService] = None

        # Latest annotated frame for MJPEG streaming (thread-safe)
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()

        # Performance counters
        self.frame_count = 0
        self.fps = 0.0
        self.start_time = time.time()
        self._critical_count = 0
        self._warning_count = 0
        self._normal_count = 0
        self._last_inference_ms = 0.0

        # HTTP session – reuse connections for lower latency
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

        print(f"⏱️  PPE Memory Window: {PPE_MEMORY_WINDOW_SECONDS}s")
        print(f"✅ RemotePipeline [{stream_id}] initialized\n")

    # ── Compat stubs (InferencePipeline parity) ───────────────────────────────

    def set_model_lock(self, _lock: threading.Lock) -> None:  # noqa: D401
        """No-op: remote mode has no shared YOLO model lock."""

    def start_logger(self) -> None:
        self.logger.start()

    def stop_logger(self) -> None:
        self.logger.stop()

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Return the most recent annotated frame (thread-safe)."""
        with self._frame_lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    # ── Core methods ──────────────────────────────────────────────────────────

    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode an OpenCV frame as a base64 JPEG string."""
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def _call_hf_infer(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Send frame to HF Space and return raw detection list.

        Returns [] on any network / server error (non-blocking).
        """
        payload = {
            "image": self._encode_frame(frame),
            "conf":  self.conf_threshold,
            "imgsz": self.img_size,
        }
        try:
            resp = self._session.post(
                self.infer_url, json=payload, timeout=self.request_timeout
            )
            resp.raise_for_status()
            data = resp.json()
            self._last_inference_ms = data.get("inference_ms", 0.0)
            return data.get("detections", [])
        except requests.exceptions.Timeout:
            print(f"[{self.stream_id}] ⚠️  HF inference timeout ({self.request_timeout}s)")
        except requests.exceptions.ConnectionError:
            print(f"[{self.stream_id}] ⚠️  HF Space unreachable: {self.infer_url}")
        except Exception as exc:  # noqa: BLE001
            print(f"[{self.stream_id}] ⚠️  Inference error: {exc}")
        return []

    def _split_detections(
        self, detections: List[Dict[str, Any]]
    ) -> tuple[List[Dict], List[Dict]]:
        """Split detections into persons and PPE items."""
        persons = [d for d in detections if d["class"] == "Person"]
        ppe = [d for d in detections if d["class"] != "Person"]
        return persons, ppe

    def process_frame(
        self, frame: np.ndarray
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a single frame through the remote pipeline.

        1. Encode + POST frame to HF Space → detections[]
        2. Track persons locally (CentroidTracker)
        3. Evaluate PPE violations locally (ViolationEngine)
        4. Enqueue violations to logger (non-blocking)
        5. Render annotated frame

        Returns:
            (annotated_frame, stats_dict)
        """
        frame_start = time.time()

        # 1. Remote YOLO inference
        detections = self._call_hf_infer(frame)

        # 2. Split into persons vs PPE
        persons, ppe_detections = self._split_detections(detections)

        # 3. Track persons
        tracked_persons = self.tracker.update(persons)

        # 4. Evaluate violations
        frame_height = frame.shape[0]
        violations = self.violation_engine.evaluate(
            tracked_persons, ppe_detections, frame_height
        )

        # 5. Log violations (non-blocking)
        for violation in violations:
            is_critical = violation.get("helmet_violation") and violation.get("vest_violation")
            has_violations = bool(violation.get("violations"))

            if is_critical:
                self.logger.enqueue(violation, frame, save_image=True)
                if self.file_logger:
                    self.file_logger.log_critical(
                        violation["person_id"], violation.get("violations", [])
                    )
                self._critical_count += 1
            elif has_violations:
                self.logger.enqueue(violation, frame, save_image=False)
                if self.file_logger:
                    self.file_logger.log_warning(
                        violation["person_id"], violation.get("violations", [])
                    )
                self._warning_count += 1

        if self.file_logger:
            violating_ids = {v["person_id"] for v in violations}
            for person in tracked_persons:
                if person["person_id"] not in violating_ids:
                    self.file_logger.log_normal(person["person_id"])
                    self._normal_count += 1

        # 6. Annotate frame
        annotated_frame = self._render_frame(frame, tracked_persons, violations, detections)

        # Update performance counters
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        self.fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        frame_time_ms = (time.time() - frame_start) * 1000

        stats = {
            "fps": round(self.fps, 1),
            "frame_time": round(frame_time_ms, 1),
            "inference_ms": round(self._last_inference_ms, 1),
            "detections": len(detections),
            "persons": len(tracked_persons),
            "violations": len(violations),
            "queue_size": self.logger.get_queue_size(),
        }

        return annotated_frame, stats

    # ── Rendering (mirrors InferencePipeline._render_frame) ──────────────────

    def _render_frame(
        self,
        frame: np.ndarray,
        tracked_persons: list,
        violations: list,
        all_detections: list,
    ) -> np.ndarray:
        annotated = frame.copy()
        violation_map = {v["person_id"]: v for v in violations}

        for person in tracked_persons:
            person_id = person["person_id"]
            x1, y1, x2, y2 = map(int, person["bbox"])

            if person_id in violation_map:
                v = violation_map[person_id]
                severity = v.get("severity", "WARNING")
                color = (0, 0, 255) if severity == "CRITICAL" else (0, 165, 255)
                label = f"Person {person_id} - {severity}"
                violations_text = ", ".join(v.get("violations", []))

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated, (x1, y1 - 20), (x1 + label_size[0], y1), color, -1)
                cv2.putText(annotated, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(annotated, f"Missing: {violations_text}", (x1, y2 + 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            else:
                color = (0, 255, 0)
                label = f"Person {person_id} - OK"
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        for det in all_detections:
            if det["class"] != "Person":
                x1, y1, x2, y2 = map(int, det["bbox"])
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 255, 0), 1)
                cv2.putText(annotated, det["class"], (x1, y1 - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 0), 1)

        self._draw_stats_overlay(annotated)
        return annotated

    def _draw_stats_overlay(self, frame: np.ndarray) -> None:
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (280, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        stats_text = [
            f"[{self.stream_id}] REMOTE",
            f"FPS: {self.fps:.1f}",
            f"Frames: {self.frame_count}",
            f"Tracked: {self.tracker.get_active_count()}",
            f"HF latency: {self._last_inference_ms:.0f}ms",
            f"Queue: {self.logger.get_queue_size()}",
        ]
        y = 30
        for text in stats_text:
            cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            y += 20

    # ── Video loop (same API as InferencePipeline.run_video) ─────────────────

    def run_video(self, source, display: bool = True) -> None:
        """Run inference on a video source (webcam, file, or RTSP URL)."""
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"❌ Error opening video source: {source}")
            return

        print(f"📹 [{self.stream_id}] Starting remote inference on: {source}")
        print("Press 'q' to quit\n")

        self.file_logger = FileLogService(video_source=source)
        self.start_logger()

        window_title = f"SafeSight AI (remote) - {self.stream_id}"

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print(f"📹 [{self.stream_id}] End of video stream")
                    break

                annotated_frame, stats = self.process_frame(frame)

                with self._frame_lock:
                    self._latest_frame = annotated_frame

                if display:
                    cv2.imshow(window_title, annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print(f"\n⏹️  [{self.stream_id}] User requested stop")
                        break

                if self.frame_count % 30 == 0:
                    print(
                        f"[{self.stream_id}] FPS: {stats['fps']} | "
                        f"HF: {stats['inference_ms']}ms | "
                        f"Persons: {stats['persons']} | "
                        f"Violations: {stats['violations']}"
                    )
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.stop_logger()

            if self.file_logger:
                self.file_logger.log_summary(
                    total_frames=self.frame_count,
                    avg_fps=self.fps,
                    critical_count=self._critical_count,
                    warning_count=self._warning_count,
                    normal_count=self._normal_count,
                )
                self.file_logger.close()

            with self._frame_lock:
                self._latest_frame = None

            print(f"\n✅ [{self.stream_id}] Done. Processed {self.frame_count} frames @ {self.fps:.1f} FPS")

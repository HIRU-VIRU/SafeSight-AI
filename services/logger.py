"""
Non-blocking violation logger for SafeSight AI.
Uses queue and background thread to prevent blocking the main inference loop.
"""

import time
import threading
from queue import Queue
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
from config.settings import DUPLICATE_COOLDOWN_SECONDS, CAMERA_ID
from services.database import DatabaseService
from services.storage import EvidenceStorage
from services.alert import AlertManager


class ViolationLogger:
    """
    Non-blocking violation logger with duplicate prevention.
    Uses background thread and queue to handle logging asynchronously.
    """
    
    def __init__(self, 
                 camera_id: str = CAMERA_ID,
                 cooldown_seconds: int = DUPLICATE_COOLDOWN_SECONDS):
        """
        Initialize violation logger.
        
        Args:
            camera_id: Camera identifier
            cooldown_seconds: Seconds to wait before logging same person again
        """
        self.camera_id = camera_id
        self.cooldown_seconds = cooldown_seconds
        
        # Services
        self.db = DatabaseService()
        self.storage = EvidenceStorage()
        self.alert = AlertManager()
        
        # Queue for async processing
        self.queue = Queue(maxsize=100)
        
        # Duplicate tracking
        self.last_logged = {}  # {person_id: timestamp}
        self.lock = threading.Lock()
        
        # Background thread
        self.running = False
        self.thread = None
        
        print("✅ ViolationLogger initialized")
    
    def start(self):
        """Start background logging thread."""
        if self.running:
            print("⚠️  Logger already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        print("✅ ViolationLogger thread started")
    
    def stop(self):
        """Stop background logging thread."""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for queue to empty
        print("⏳ Waiting for logging queue to empty...")
        self.queue.join()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("✅ ViolationLogger stopped")
    
    def enqueue(self, violation: Dict[str, Any], frame: np.ndarray, save_image: bool = True):
        """
        Add violation to processing queue (non-blocking).
        
        Args:
            violation: Violation dictionary with person_id and violation flags
            frame: Video frame as numpy array
            save_image: Whether to save an evidence image (True for critical)
        """
        person_id = violation["person_id"]
        
        # Check for duplicate
        if self._is_duplicate(person_id):
            return  # Skip duplicate
        
        # Add to queue
        try:
            self.queue.put_nowait({
                "violation": violation,
                "frame": frame.copy(),  # Copy to avoid race conditions
                "timestamp": time.time(),
                "save_image": save_image,
            })
        except:
            print("⚠️  Logging queue full, dropping violation")
    
    def _is_duplicate(self, person_id: int) -> bool:
        """
        Check if person was recently logged (within cooldown period).
        
        Args:
            person_id: Tracked person ID
            
        Returns:
            True if duplicate, False otherwise
        """
        with self.lock:
            now = time.time()
            
            if person_id in self.last_logged:
                last_time = self.last_logged[person_id]
                if (now - last_time) < self.cooldown_seconds:
                    return True  # Duplicate
            
            # Update last logged time
            self.last_logged[person_id] = now
            return False
    
    def _process_queue(self):
        """Background thread that processes violation queue."""
        print("🔄 Logger processing thread active")
        
        while self.running or not self.queue.empty():
            try:
                # Get item from queue with timeout
                item = self.queue.get(timeout=1)
                
                # Process violation
                self._log_violation(
                    item["violation"],
                    item["frame"],
                    save_image=item.get("save_image", True),
                )
                
                self.queue.task_done()
                
            except:
                # Queue empty or timeout
                continue
        
        print("🔄 Logger processing thread stopped")
    
    def _log_violation(self, violation: Dict[str, Any], frame: np.ndarray, save_image: bool = True):
        """
        Log violation to database, optionally save image, and trigger alert.
        
        Args:
            violation: Violation data
            frame: Video frame
            save_image: Whether to save an evidence image
        """
        try:
            # 1. Save violation image (only for critical)
            image_path = None
            if save_image:
                image_path = self.storage.save_violation_image(
                    frame=frame,
                    bbox=violation["bbox"],
                    camera_id=self.camera_id,
                    person_id=violation["person_id"]
                )
            
            # 2. Insert into database
            violation_id = self.db.insert_violation(
                violation=violation,
                camera_id=self.camera_id,
                image_path=image_path or ""
            )
            
            # 3. Trigger alert
            self.alert.send_alert(violation, self.camera_id)
            
            # Log success
            violations_text = ", ".join(violation.get("violations", []))
            severity = violation.get("severity", "WARNING")
            print(f"\U0001f4dd [{severity}] Violation #{violation_id} - Person {violation['person_id']}: {violations_text}")
            
        except Exception as e:
            print(f"❌ Error logging violation: {e}")
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def cleanup_old_duplicates(self, max_age_seconds: int = 300):
        """
        Remove old entries from duplicate tracking dictionary.
        
        Args:
            max_age_seconds: Remove entries older than this (default 5 minutes)
        """
        with self.lock:
            now = time.time()
            to_remove = [
                person_id for person_id, timestamp in self.last_logged.items()
                if (now - timestamp) > max_age_seconds
            ]
            
            for person_id in to_remove:
                del self.last_logged[person_id]
            
            if len(to_remove) > 0:
                print(f"🧹 Cleaned up {len(to_remove)} old duplicate entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        return {
            "queue_size": self.get_queue_size(),
            "tracked_persons": len(self.last_logged),
            "running": self.running
        }

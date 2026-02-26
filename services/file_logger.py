"""
File-based logging service for SafeSight AI.
Writes CRITICAL, WARNING, and NORMAL events to separate log files,
one set of files per video session.
"""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config.settings import LOG_PATH, CAMERA_ID, PPE_MEMORY_WINDOW_SECONDS


class FileLogService:
    """
    Writes structured logs to per-session files split by severity.

    Files created per session::

        logs/<video_name>_<timestamp>/
            critical.log
            warning.log
            normal.log
            session_info.log      ← config snapshot
    """

    def __init__(self, video_source: str, camera_id: str = CAMERA_ID):
        """
        Args:
            video_source: Path / URL of the video being processed.
            camera_id: Camera identifier.
        """
        self.camera_id = camera_id
        self.video_source = video_source
        self.lock = threading.Lock()

        # Derive a short name for the session folder
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = Path(str(video_source)).stem if not str(video_source).startswith(("http", "rtsp")) else "stream"
        # Truncate long names
        video_name = video_name[:60]
        self.session_dir = Path(LOG_PATH) / f"{video_name}_{ts}"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Open the three log files
        self._files: Dict[str, Any] = {}
        for level in ("critical", "warning", "normal"):
            fpath = self.session_dir / f"{level}.log"
            self._files[level] = open(fpath, "a", encoding="utf-8")

        # Write session info header
        self._write_session_info()

        print(f"📄 File logs → {self.session_dir}")

    # ------------------------------------------------------------------ public

    def log_critical(self, person_id: int, violations: List[str],
                     extra: Optional[Dict[str, Any]] = None):
        """Log a CRITICAL violation (helmet + vest missing)."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{ts}] CRITICAL | Camera: {self.camera_id} | "
                f"Person {person_id} | Missing: {', '.join(violations)}")
        if extra:
            line += f" | {extra}"
        self._write("critical", line)

    def log_warning(self, person_id: int, violations: List[str],
                    extra: Optional[Dict[str, Any]] = None):
        """Log a WARNING violation (optional PPE missing)."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{ts}] WARNING  | Camera: {self.camera_id} | "
                f"Person {person_id} | Missing: {', '.join(violations)}")
        if extra:
            line += f" | {extra}"
        self._write("warning", line)

    def log_normal(self, person_id: int):
        """Log that a person is fully compliant."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = (f"[{ts}] NORMAL   | Camera: {self.camera_id} | "
                f"Person {person_id} | All PPE OK")
        self._write("normal", line)

    def log_summary(self, total_frames: int, avg_fps: float,
                    critical_count: int, warning_count: int, normal_count: int):
        """Append a summary block to all three files."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = (
            f"\n{'=' * 60}\n"
            f"SESSION SUMMARY  ({ts})\n"
            f"{'=' * 60}\n"
            f"Video: {self.video_source}\n"
            f"Total Frames: {total_frames}\n"
            f"Average FPS: {avg_fps:.1f}\n"
            f"Memory Window: {PPE_MEMORY_WINDOW_SECONDS}s\n"
            f"Critical Events: {critical_count}\n"
            f"Warning Events: {warning_count}\n"
            f"Normal Events: {normal_count}\n"
            f"{'=' * 60}\n"
        )
        for level in ("critical", "warning", "normal"):
            self._write(level, summary)

    def close(self):
        """Flush and close all log files."""
        with self.lock:
            for f in self._files.values():
                try:
                    f.flush()
                    f.close()
                except Exception:
                    pass
        print(f"📄 Logs saved to {self.session_dir}")

    # ------------------------------------------------------------------ internal

    def _write(self, level: str, line: str):
        with self.lock:
            f = self._files.get(level)
            if f and not f.closed:
                f.write(line + "\n")
                f.flush()

    def _write_session_info(self):
        """Write config snapshot at session start."""
        info_path = self.session_dir / "session_info.log"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"SafeSight AI – Session Log\n")
            f.write(f"{'=' * 50}\n")
            f.write(f"Started: {ts}\n")
            f.write(f"Video: {self.video_source}\n")
            f.write(f"Camera: {self.camera_id}\n")
            f.write(f"PPE Memory Window: {PPE_MEMORY_WINDOW_SECONDS}s\n")
            f.write(f"{'=' * 50}\n\n")

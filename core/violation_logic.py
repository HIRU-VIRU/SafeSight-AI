"""
Intelligent violation detection logic for SafeSight AI.
Evaluates PPE compliance with temporal smoothing, PPE priority levels,
and visibility heuristics to prevent false-positive spam.
"""

import time
from typing import List, Dict, Any
from config.settings import (
    IOU_THRESHOLD,
    MANDATORY_PPE,
    OPTIONAL_PPE,
    MIN_VIOLATION_FRAMES,
    MIN_VISIBLE_HEIGHT,
    FRAME_BOTTOM_MARGIN,
    PPE_MEMORY_WINDOW_SECONDS,
)


class ViolationEngine:
    """
    PPE violation detection engine with:
      - IoU-based overlap to decide whether PPE is worn
      - MANDATORY vs OPTIONAL PPE severity levels
      - Per-person temporal smoothing (must miss N consecutive frames)
      - Visibility heuristics (boots / goggles skip when not visible)
    """

    def __init__(self,
                 iou_threshold: float = IOU_THRESHOLD,
                 min_violation_frames: int = MIN_VIOLATION_FRAMES,
                 memory_window: float = PPE_MEMORY_WINDOW_SECONDS):
        """
        Args:
            iou_threshold: Minimum containment ratio for PPE-person overlap.
            min_violation_frames: Consecutive frames PPE must be missing
                                  (after memory window expires) before a
                                  violation is confirmed.
            memory_window: Seconds to remember a positive PPE detection.
                           While the window is active the person stays OK.
        """
        self.iou_threshold = iou_threshold
        self.min_violation_frames = min_violation_frames
        self.memory_window = memory_window
        self.mandatory_ppe = MANDATORY_PPE
        self.optional_ppe = OPTIONAL_PPE
        self.all_ppe = self.mandatory_ppe + self.optional_ppe

        # Per-person temporal state  {person_id: {ppe_type: missing_frame_count}}
        self._state: Dict[int, Dict[str, int]] = {}

        # Positive memory  {person_id: {ppe_type: last_seen_timestamp}}
        self._last_seen: Dict[int, Dict[str, float]] = {}

    # ------------------------------------------------------------------ IoU

    @staticmethod
    def compute_iou(bbox1: List[float], bbox2: List[float]) -> float:
        """Compute Intersection over Union between two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        inter = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - inter
        return inter / union if union > 0 else 0.0

    @staticmethod
    def compute_containment(person_bbox: List[float], ppe_bbox: List[float]) -> float:
        """
        Compute what fraction of the PPE bbox is inside the person bbox.

        This is far more appropriate than IoU for matching small PPE items
        (helmet, gloves) against a large person bounding box.

        Returns:
            Ratio in [0, 1]. 1.0 means the PPE box is fully inside the person box.
        """
        x1_p, y1_p, x2_p, y2_p = person_bbox
        x1_e, y1_e, x2_e, y2_e = ppe_bbox

        x1_i = max(x1_p, x1_e)
        y1_i = max(y1_p, y1_e)
        x2_i = min(x2_p, x2_e)
        y2_i = min(y2_p, y2_e)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        inter = (x2_i - x1_i) * (y2_i - y1_i)
        ppe_area = (x2_e - x1_e) * (y2_e - y1_e)
        return inter / ppe_area if ppe_area > 0 else 0.0

    def _has_ppe_overlap(self, person_bbox: List[float],
                         ppe_bboxes: List[List[float]]) -> bool:
        """
        Return True if any PPE bbox is sufficiently contained within the person bbox.

        Uses containment ratio (intersection / ppe_area) instead of IoU because
        PPE boxes (helmet, gloves …) are much smaller than the person box,
        making IoU unreliable.
        """
        for ppe_bbox in ppe_bboxes:
            if self.compute_containment(person_bbox, ppe_bbox) >= self.iou_threshold:
                return True
        return False

    # ------------------------------------------------------------------ visibility heuristics

    @staticmethod
    def _should_skip_boots(person_bbox: List[float],
                           frame_height: int) -> bool:
        """
        Skip boots check when the person's lower body is likely cropped.
        Conditions:
          - Person bbox bottom is within FRAME_BOTTOM_MARGIN of frame bottom
          - Person bbox height < MIN_VISIBLE_HEIGHT
        """
        _, y1, _, y2 = person_bbox
        bbox_h = y2 - y1

        if bbox_h < MIN_VISIBLE_HEIGHT:
            return True
        if (frame_height - y2) < FRAME_BOTTOM_MARGIN:
            return True
        return False

    @staticmethod
    def _should_skip_goggles(person_bbox: List[float],
                             frame_height: int) -> bool:
        """
        Skip goggles check when the upper-face region is likely not visible.
        Heuristic: person bbox top is very close to frame top
          or the bbox is very small.
        """
        _, y1, _, y2 = person_bbox
        bbox_h = y2 - y1

        if bbox_h < MIN_VISIBLE_HEIGHT:
            return True
        if y1 < FRAME_BOTTOM_MARGIN:
            return True
        return False

    # ------------------------------------------------------------------ temporal state

    def _get_person_state(self, person_id: int) -> Dict[str, int]:
        if person_id not in self._state:
            self._state[person_id] = {ppe: 0 for ppe in self.all_ppe}
        return self._state[person_id]

    def _get_last_seen(self, person_id: int) -> Dict[str, float]:
        if person_id not in self._last_seen:
            self._last_seen[person_id] = {ppe: 0.0 for ppe in self.all_ppe}
        return self._last_seen[person_id]

    def _ppe_in_memory(self, person_id: int, ppe_type: str) -> bool:
        """Return True if this PPE was seen on this person within the memory window."""
        last = self._get_last_seen(person_id).get(ppe_type, 0.0)
        return (time.time() - last) < self.memory_window

    def cleanup_stale(self, active_ids: set):
        """Remove temporal state for persons no longer tracked."""
        stale = [pid for pid in self._state if pid not in active_ids]
        for pid in stale:
            del self._state[pid]
        stale_mem = [pid for pid in self._last_seen if pid not in active_ids]
        for pid in stale_mem:
            del self._last_seen[pid]

    # ------------------------------------------------------------------ evaluate

    def evaluate(self,
                 tracked_persons: List[Dict[str, Any]],
                 ppe_detections: Dict[str, List[Dict[str, Any]]],
                 frame_height: int = 0) -> List[Dict[str, Any]]:
        """
        Evaluate PPE violations for all tracked persons.

        Args:
            tracked_persons: [{"person_id": int, "bbox": [x1,y1,x2,y2]}]
            ppe_detections:  {"helmet": [{...}], "vest": [{...}], ...}
            frame_height:    Height of the current frame (for visibility heuristics).

        Returns:
            List of confirmed violations::

                [
                    {
                        "person_id": 3,
                        "severity": "CRITICAL" | "WARNING",
                        "helmet_violation": True,
                        "vest_violation": False,
                        ...
                        "violations": ["helmet"],
                        "bbox": [...]
                    }
                ]
        """
        violations: List[Dict[str, Any]] = []
        active_ids = {p["person_id"] for p in tracked_persons}

        for person in tracked_persons:
            pid = person["person_id"]
            bbox = person["bbox"]
            state = self._get_person_state(pid)

            confirmed: List[str] = []
            result: Dict[str, Any] = {
                "person_id": pid,
                "bbox": bbox,
            }

            for ppe_type in self.all_ppe:
                # --- visibility heuristic skip ---
                if frame_height > 0:
                    if ppe_type == "boots" and self._should_skip_boots(bbox, frame_height):
                        state[ppe_type] = 0  # reset – can't judge
                        result[f"{ppe_type}_violation"] = False
                        continue
                    if ppe_type == "goggles" and self._should_skip_goggles(bbox, frame_height):
                        state[ppe_type] = 0
                        result[f"{ppe_type}_violation"] = False
                        continue

                ppe_items = ppe_detections.get(ppe_type, [])
                ppe_bboxes = [item["bbox"] for item in ppe_items]
                has_ppe = self._has_ppe_overlap(bbox, ppe_bboxes)

                last_seen = self._get_last_seen(pid)

                if has_ppe:
                    # PPE detected right now – reset counter & record timestamp
                    state[ppe_type] = 0
                    last_seen[ppe_type] = time.time()
                    result[f"{ppe_type}_violation"] = False
                elif self._ppe_in_memory(pid, ppe_type):
                    # Not detected this frame, but was seen recently – stay OK
                    state[ppe_type] = 0
                    result[f"{ppe_type}_violation"] = False
                else:
                    # Not detected and memory window expired – start counting
                    state[ppe_type] += 1
                    if state[ppe_type] >= self.min_violation_frames:
                        confirmed.append(ppe_type)
                        result[f"{ppe_type}_violation"] = True
                    else:
                        result[f"{ppe_type}_violation"] = False

            if not confirmed:
                continue

            # --- determine severity ---
            has_mandatory = any(v in self.mandatory_ppe for v in confirmed)
            result["severity"] = "CRITICAL" if has_mandatory else "WARNING"
            result["violations"] = confirmed
            violations.append(result)

        # Garbage-collect state for deregistered persons
        self.cleanup_stale(active_ids)

        return violations

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def has_any_violation(violation_result: Dict[str, Any]) -> bool:
        """Check if a violation result has any violations."""
        return len(violation_result.get("violations", [])) > 0

    @staticmethod
    def format_violations_text(violations: List[str]) -> str:
        """Format list of violations as comma-separated text."""
        return ", ".join(violations) if violations else "none"

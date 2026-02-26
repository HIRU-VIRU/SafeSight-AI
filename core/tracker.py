"""
Stable person tracker with lost-track re-ID buffer, combined
IoU+distance matching, bbox EMA smoothing and tentative promotion.

Core improvements over v1:
  - Lost-track buffer: expired confirmed tracks are kept for
    ``max_lost_age`` frames. Re-appearing persons recover their
    original ID instead of being assigned a new one.
  - Single-pass combined scoring (IoU + height-normalised distance)
    replaces the sequential IoU-then-centroid strategy, giving more
    globally consistent assignments.
  - Bbox EMA smoothing removes per-frame jitter without lag.
  - min_hits=3 for faster ID stabilisation on entry.
  - Velocity prediction uses a slower EMA (alpha=0.2) to avoid
    overshooting on noisy detections.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from config.settings import (
    TRACKER_MAX_DISAPPEARED,
    TRACKER_IOU_MATCH_THRESHOLD,
    TRACKER_MAX_CENTROID_DISTANCE,
)


# ────────────────────────────── geometry helpers ──────────────────────────────

def _centroid(bbox: List[float]) -> Tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def _iou(a: List[float], b: List[float]) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _box_height(bbox: List[float]) -> float:
    return max(bbox[3] - bbox[1], 1.0)


def _combined_score(
    trk_bbox: List[float],
    det_bbox: List[float],
    max_dist: float,
) -> float:
    """
    Combined similarity in [0, 1].
    score = 0.55 * iou  +  0.45 * (1 - normalised_centroid_distance)
    The centroid distance is normalised by the track's bbox height so
    the threshold is scale-invariant.
    """
    iou_score = _iou(trk_bbox, det_bbox)

    tc = _centroid(trk_bbox)
    dc = _centroid(det_bbox)
    pixel_dist = ((tc[0] - dc[0]) ** 2 + (tc[1] - dc[1]) ** 2) ** 0.5

    # Normalise by max of the two heights so large/small persons are treated fairly
    scale = max(_box_height(trk_bbox), _box_height(det_bbox))
    norm_dist = pixel_dist / max(scale * 2.0, 1.0)   # 2x height = generous budget
    dist_score = max(0.0, 1.0 - norm_dist)

    return 0.55 * iou_score + 0.45 * dist_score


# ────────────────────────── assignment (greedy on combined score) ─────────────

def _assign(
    trk_ids: List[int],
    trk_bboxes: List[List[float]],
    det_bboxes: List[List[float]],
    min_score: float,
    max_dist: float,
) -> Dict[int, int]:
    """
    Single-pass greedy assignment on the combined score matrix.
    Returns: {det_idx: trk_id}
    """
    if not trk_ids or not det_bboxes:
        return {}

    n_t, n_d = len(trk_ids), len(det_bboxes)
    score_mat = np.zeros((n_t, n_d), dtype=np.float32)
    for ti in range(n_t):
        for di in range(n_d):
            score_mat[ti, di] = _combined_score(trk_bboxes[ti], det_bboxes[di], max_dist)

    result: Dict[int, int] = {}
    used_t: set = set()
    used_d: set = set()

    # Sort all (ti, di) pairs by score descending, greedily pick non-conflicting
    flat_order = np.argsort(score_mat.ravel())[::-1]
    for idx in flat_order:
        ti, di = divmod(int(idx), n_d)
        if ti in used_t or di in used_d:
            continue
        if score_mat[ti, di] < min_score:
            break
        result[di] = trk_ids[ti]
        used_t.add(ti)
        used_d.add(di)

    return result


# ──────────────────────────────── tracker ─────────────────────────────────────

class CentroidTracker:
    """
    Person tracker with lost-track re-ID buffer.

    Track lifecycle:
        detection -> tentative (needs min_hits consecutive frames)
                  -> confirmed (returned to consumers)
                  -> lost (kept for max_lost_age frames after expiry)
                  -> deleted

    If a confirmed track expires it moves to the *lost* buffer.
    Unmatched detections first attempt to re-match against lost tracks
    with a wider distance budget.  A match restores the original ID.
    """

    def __init__(
        self,
        max_disappeared: int = TRACKER_MAX_DISAPPEARED,
        iou_match_threshold: float = TRACKER_IOU_MATCH_THRESHOLD,
        max_centroid_distance: float = TRACKER_MAX_CENTROID_DISTANCE,
        min_hits: int = 3,
        max_lost_age: int = 90,          # ~3 s at 30 fps
        bbox_smooth_alpha: float = 0.55, # EMA weight for new bbox
    ):
        self.max_disappeared = max_disappeared
        self.min_score = max(0.10, iou_match_threshold * 0.5)
        self.max_dist = max_centroid_distance
        self.min_hits = min_hits
        self.max_lost_age = max_lost_age
        self.bbox_alpha = bbox_smooth_alpha

        self.next_id = 1

        # confirmed: {id: {bbox, centroid, missing_frames, velocity}}
        self.objects: Dict[int, Dict[str, Any]] = {}
        # tentative: same + hits
        self.tentative: Dict[int, Dict[str, Any]] = {}
        # recently lost confirmed tracks (for re-ID)
        self.lost: Dict[int, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ update

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        det_bboxes = [d["bbox"] for d in detections] if detections else []

        if not det_bboxes:
            self._age_all()
            return self._output()

        if not self.objects and not self.tentative and not self.lost:
            for bb in det_bboxes:
                self._new_tentative(bb)
            return self._output()

        used_det: set = set()

        # ── 1. Match detections -> confirmed tracks ───────────────────────────
        matched_conf: set = set()
        if self.objects:
            c_ids = list(self.objects.keys())
            c_pred = [self._predict(self.objects[oid]) for oid in c_ids]
            for di, oid in _assign(c_ids, c_pred, det_bboxes, self.min_score, self.max_dist).items():
                self._refresh_confirmed(oid, det_bboxes[di])
                used_det.add(di)
                matched_conf.add(oid)

        # ── 2. Re-ID: match remaining detections -> lost tracks ───────────────
        rem_idx = sorted(set(range(len(det_bboxes))) - used_det)
        if rem_idx and self.lost:
            rem_bb = [det_bboxes[i] for i in rem_idx]
            l_ids = list(self.lost.keys())
            l_bb = [self.lost[lid]["bbox"] for lid in l_ids]
            # Wider thresholds for re-ID (person may have moved more)
            for ri, lid in _assign(l_ids, l_bb, rem_bb, self.min_score * 0.7, self.max_dist * 2.0).items():
                bb = rem_bb[ri]
                self.objects[lid] = {
                    "bbox": bb,
                    "centroid": _centroid(bb),
                    "missing_frames": 0,
                    "velocity": self.lost[lid].get("velocity", (0.0, 0.0)),
                }
                del self.lost[lid]
                used_det.add(rem_idx[ri])
                matched_conf.add(lid)

        # ── 3. Match remaining -> tentative tracks ────────────────────────────
        rem_idx = sorted(set(range(len(det_bboxes))) - used_det)
        matched_tent: set = set()
        if rem_idx and self.tentative:
            rem_bb = [det_bboxes[i] for i in rem_idx]
            t_ids = list(self.tentative.keys())
            t_bb = [self.tentative[tid]["bbox"] for tid in t_ids]
            for ri, tid in _assign(t_ids, t_bb, rem_bb, self.min_score, self.max_dist).items():
                bb = rem_bb[ri]
                t = self.tentative[tid]
                t["bbox"] = bb
                t["centroid"] = _centroid(bb)
                t["hits"] += 1
                t["missing_frames"] = 0
                matched_tent.add(tid)
                used_det.add(rem_idx[ri])
                if t["hits"] >= self.min_hits:
                    self._promote(tid)
                    matched_conf.add(tid)

        # ── 4. Truly new detections -> tentative ─────────────────────────────
        for di in sorted(set(range(len(det_bboxes))) - used_det):
            self._new_tentative(det_bboxes[di])

        # ── 5. Age unmatched confirmed (may expire -> lost buffer) ────────────
        for oid in list(set(self.objects.keys()) - matched_conf):
            self.objects[oid]["missing_frames"] += 1
            if self.objects[oid]["missing_frames"] > self.max_disappeared:
                self.lost[oid] = {
                    "bbox": self.objects[oid]["bbox"],
                    "centroid": self.objects[oid]["centroid"],
                    "velocity": self.objects[oid].get("velocity", (0.0, 0.0)),
                    "lost_age": 0,
                }
                del self.objects[oid]

        # ── 6. Age unmatched tentative ────────────────────────────────────────
        for tid in list(set(self.tentative.keys()) - matched_tent):
            self.tentative[tid]["missing_frames"] += 1
            if self.tentative[tid]["missing_frames"] > 8:
                del self.tentative[tid]

        # ── 7. Age lost buffer ────────────────────────────────────────────────
        for lid in list(self.lost.keys()):
            self.lost[lid]["lost_age"] += 1
            if self.lost[lid]["lost_age"] > self.max_lost_age:
                del self.lost[lid]

        return self._output()

    # ------------------------------------------------------------------ internal helpers

    def _new_tentative(self, bbox: List[float]):
        oid = self.next_id
        self.tentative[oid] = {
            "bbox": bbox,
            "centroid": _centroid(bbox),
            "missing_frames": 0,
            "velocity": (0.0, 0.0),
            "hits": 1,
        }
        self.next_id += 1

    def _promote(self, tid: int):
        t = self.tentative.pop(tid)
        self.objects[tid] = {
            "bbox": t["bbox"],
            "centroid": t["centroid"],
            "missing_frames": 0,
            "velocity": t.get("velocity", (0.0, 0.0)),
        }

    def _predict(self, obj: Dict[str, Any]) -> List[float]:
        """Shift bbox by last known velocity for better frame-ahead matching."""
        b = obj["bbox"]
        vx, vy = obj.get("velocity", (0.0, 0.0))
        return [b[0] + vx, b[1] + vy, b[2] + vx, b[3] + vy]

    def _refresh_confirmed(self, oid: int, new_bbox: List[float]):
        """EMA-smooth bbox and update slow velocity estimate."""
        obj = self.objects[oid]
        old_b = obj["bbox"]
        alpha = self.bbox_alpha

        smoothed = [
            alpha * new_bbox[i] + (1 - alpha) * old_b[i]
            for i in range(4)
        ]

        old_c = obj["centroid"]
        new_c = _centroid(smoothed)

        vel_alpha = 0.2   # slow EMA avoids overreacting to jitter
        ovx, ovy = obj.get("velocity", (0.0, 0.0))
        obj["velocity"] = (
            vel_alpha * (new_c[0] - old_c[0]) + (1 - vel_alpha) * ovx,
            vel_alpha * (new_c[1] - old_c[1]) + (1 - vel_alpha) * ovy,
        )
        obj["bbox"] = smoothed
        obj["centroid"] = new_c
        obj["missing_frames"] = 0

    def _age_all(self):
        """Called when there are no detections this frame."""
        for oid in list(self.objects):
            self.objects[oid]["missing_frames"] += 1
            if self.objects[oid]["missing_frames"] > self.max_disappeared:
                self.lost[oid] = {
                    "bbox": self.objects[oid]["bbox"],
                    "centroid": self.objects[oid]["centroid"],
                    "velocity": self.objects[oid].get("velocity", (0.0, 0.0)),
                    "lost_age": 0,
                }
                del self.objects[oid]

        for tid in list(self.tentative):
            self.tentative[tid]["missing_frames"] += 1
            if self.tentative[tid]["missing_frames"] > 8:
                del self.tentative[tid]

        for lid in list(self.lost):
            self.lost[lid]["lost_age"] += 1
            if self.lost[lid]["lost_age"] > self.max_lost_age:
                del self.lost[lid]

    def _output(self) -> List[Dict[str, Any]]:
        return [
            {"person_id": oid, "bbox": list(obj["bbox"])}
            for oid, obj in self.objects.items()
        ]

    # ------------------------------------------------------------------ public helpers

    def get_active_count(self) -> int:
        return len(self.objects)

    def reset(self):
        self.objects.clear()
        self.tentative.clear()
        self.lost.clear()
        self.next_id = 1

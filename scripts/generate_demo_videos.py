#!/usr/bin/env python3
"""
generate_demo_videos.py
-----------------------
Runs SafeSight AI inference on 4 selected construction-site videos and saves
the annotated output as MP4 files under  storage/demo/.

Usage (from project root, with venv active):
    python scripts/generate_demo_videos.py

Output:
    storage/demo/demo_1_<stem>.mp4
    storage/demo/demo_2_<stem>.mp4
    storage/demo/demo_3_<stem>.mp4
    storage/demo/demo_4_<stem>.mp4
"""

import sys
import subprocess
import tempfile
import cv2
from pathlib import Path

# ── Make project root importable ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.inference import InferencePipeline  # noqa: E402

# ── 4 source videos (relative to project root) ────────────────────────────────
VIDEO_DIR = PROJECT_ROOT / "construction_site_videos"

SELECTED = [
    "a-team-bw.mp4",
    "construction-workers-walked-toward-camera-slow-mo-SBV-300151624-preview.mp4",
    "energetic-construction-site-with-efficient-brick-laying-in-progress-SBV-352573165-preview.mp4",
    "pouring-concrete-shots-of-civil-works-construction-equipment-and-workers-concr-SBV-347401923-preview.mp4",
]

OUTPUT_DIR = PROJECT_ROOT / "storage" / "demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FOURCC = cv2.VideoWriter_fourcc(*"mp4v")  # intermediate; re-encoded to H.264 below


def _reencode_h264(src: Path, dst: Path) -> bool:
    """Re-encode *src* (mp4v) to *dst* (H.264/avc1) using ffmpeg."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-vcodec", "libx264", "-preset", "fast", "-crf", "23",
            "-movflags", "+faststart",
            "-an",          # no audio stream
            str(dst),
        ],
        capture_output=True,
    )
    return result.returncode == 0


def process_video(src_path: Path, out_path: Path, stream_id: str, max_frames: int = 0):
    """
    Run inference on *src_path* and write annotated frames to *out_path*.

    Args:
        src_path   : Input video file.
        out_path   : Destination MP4 file.
        stream_id  : Label used in the stats overlay.
        max_frames : If > 0, stop after this many frames (useful to cap demo length).
    """
    cap = cv2.VideoCapture(str(src_path))
    if not cap.isOpened():
        print(f"  ❌  Cannot open: {src_path}")
        return False

    fps_src = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"  📹  {src_path.name}  ({w}×{h} @ {fps_src:.1f} fps,  {total} frames)")

    # Write annotated frames to a temp mp4v file first
    tmp_path = out_path.with_suffix('.tmp.mp4')
    writer = cv2.VideoWriter(str(tmp_path), FOURCC, fps_src, (w, h))

    pipeline = InferencePipeline(stream_id=stream_id)
    pipeline.start_logger()

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if max_frames > 0 and frame_idx >= max_frames:
                break

            annotated, stats = pipeline.process_frame(frame)
            writer.write(annotated)
            frame_idx += 1

            if frame_idx % 30 == 0:
                print(
                    f"    [{stream_id}]  frame {frame_idx}/{total if max_frames == 0 else max_frames}"
                    f"  |  FPS {stats['fps']:.1f}  |  violations {stats['violations']}"
                )
    finally:
        cap.release()
        writer.release()
        pipeline.stop_logger()

    # Re-encode to H.264 so browsers can play the file
    print(f"  🔄  Re-encoding to H.264 …")
    if _reencode_h264(tmp_path, out_path):
        tmp_path.unlink(missing_ok=True)
        print(f"  ✅  Saved → {out_path.name}  ({frame_idx} frames)\n")
    else:
        # Fallback: keep the mp4v file under the original name
        tmp_path.rename(out_path)
        print(f"  ⚠️   ffmpeg re-encode failed – saved raw mp4v → {out_path.name}\n")

    return True


def main():
    print("\n" + "=" * 60)
    print("  SafeSight AI – Demo Video Generator")
    print("=" * 60 + "\n")

    for idx, filename in enumerate(SELECTED, start=1):
        src = VIDEO_DIR / filename
        if not src.exists():
            print(f"  ⚠️  Skipping (not found): {src}")
            continue

        stem = src.stem[:40]  # avoid overly-long filenames
        out = OUTPUT_DIR / f"demo_{idx}_{stem}.mp4"

        if out.exists():
            print(f"  ⏩  Already processed, skipping: {out.name}\n")
            continue

        print(f"[{idx}/4] Processing …")
        process_video(src, out, stream_id=f"demo_{idx}", max_frames=0)

    print("\n" + "=" * 60)
    print("  All demo videos processed.")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

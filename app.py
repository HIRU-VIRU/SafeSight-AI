#!/usr/bin/env python3
"""
SafeSight AI - Main Application Entry Point
Real-Time Construction Safety Monitoring System

Usage:
    # Single source
    python app.py webcam
    python app.py path/to/video.mp4
    python app.py rtsp://camera_ip:port/stream

    # Multiple sources (parallel)
    python app.py video1.mp4 video2.mp4 rtsp://cam1
    
    # Run API server only
    python app.py --api-only
    
    # Run inference + API server
    python app.py webcam --with-api
"""

import sys
import argparse
import signal
import threading
from pathlib import Path
from typing import Dict, List

from ultralytics import YOLO
import torch

from config import settings
from core.inference import InferencePipeline
from api.dashboard_api import run_api_server


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              ⚡ SafeSight AI ⚡                            ║
║      Real-Time Construction Safety Monitoring            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def validate_environment():
    """Validate environment and configuration."""
    print("🔍 Validating environment...")
    
    if not settings.validate_config():
        print("❌ Configuration validation failed")
        sys.exit(1)
    
    # Check model file
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        print(f"❌ Model file not found: {settings.MODEL_PATH}")
        print("Please ensure best.pt is in the model/ directory")
        sys.exit(1)
    
    print("✅ Environment validated\n")


def _resolve_source(source: str):
    """Convert source string into something cv2.VideoCapture understands."""
    if source.lower() == "webcam":
        return 0
    if source.startswith(("http://", "https://", "rtsp://")):
        return source
    if not Path(source).exists():
        print(f"❌ Video file not found: {source}")
        sys.exit(1)
    return source


def _make_stream_id(source: str, index: int) -> str:
    """Generate a short human-readable stream label."""
    if source == 0 or str(source).lower() == "webcam":
        return "webcam"
    name = Path(str(source)).stem if not str(source).startswith(("http", "rtsp")) else str(source).split("/")[-1]
    # Truncate long names
    name = name[:40]
    return f"stream_{index}_{name}"


# ------------------------------------------------------------------ single source

def run_inference(source: str, with_api: bool = False):
    """
    Run inference pipeline on a single source.
    """
    settings.print_config()
    
    pipeline = InferencePipeline()
    
    # Start API server in background if requested
    if with_api:
        _start_api_background()
    
    video_source = _resolve_source(source)
    print(f"🎥 Video source: {video_source}\n")
    
    try:
        pipeline.run_video(video_source, display=True)
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ Shutdown complete")


# ------------------------------------------------------------------ multi source

def _detect_gpus() -> List[str]:
    """
    Detect available CUDA GPUs.
    Returns list of device strings, e.g. ['cuda:0', 'cuda:1'].
    Falls back to ['cpu'] if no GPU found.
    """
    if not torch.cuda.is_available():
        return ["cpu"]
    count = torch.cuda.device_count()
    devices = [f"cuda:{i}" for i in range(count)]
    return devices if devices else ["cpu"]


def run_multi_inference(sources: List[str], with_api: bool = False):
    """
    Run inference on multiple sources in parallel.

    GPU strategy:
    - Detects all available GPUs.
    - Loads one YOLO model copy per GPU.
    - Distributes streams round-robin across GPUs.
    - Streams sharing a GPU use a per-GPU lock (serialized inference).
    - Streams on separate GPUs run fully parallel (no lock needed).
    """
    settings.print_config()
    
    gpus = _detect_gpus()
    num_gpus = len(gpus)
    print(f"🔍 Detected {num_gpus} device(s): {gpus}")
    
    if with_api:
        _start_api_background()
    
    # Figure out which GPUs will actually be used
    used_gpus: Dict[str, int] = {}  # device -> stream count
    for i in range(len(sources)):
        dev = gpus[i % num_gpus]
        used_gpus[dev] = used_gpus.get(dev, 0) + 1
    
    # Load one model per GPU and create a lock per GPU
    gpu_models: Dict[str, YOLO] = {}
    gpu_locks: Dict[str, threading.Lock] = {}
    
    for dev in used_gpus:
        print(f"📦 Loading YOLO model on {dev}...")
        model = YOLO(settings.MODEL_PATH)
        gpu_models[dev] = model
        gpu_locks[dev] = threading.Lock()
    
    print(f"✅ {len(gpu_models)} model(s) loaded — serving {len(sources)} streams\n")
    
    # Resolve sources and assign GPUs round-robin
    resolved = []
    for i, src in enumerate(sources):
        video_source = _resolve_source(src)
        stream_id = _make_stream_id(src, i + 1)
        assigned_gpu = gpus[i % num_gpus]
        resolved.append((video_source, stream_id, assigned_gpu))
    
    # Print assignment table
    print("📋 Stream → GPU assignment:")
    for video_source, stream_id, assigned_gpu in resolved:
        print(f"   {stream_id}  →  {assigned_gpu}")
    print()
    
    # Create one pipeline per source
    threads: List[threading.Thread] = []
    
    for video_source, stream_id, assigned_gpu in resolved:
        model = gpu_models[assigned_gpu]
        
        pipeline = InferencePipeline(
            shared_model=model,
            stream_id=stream_id,
            device=assigned_gpu
        )
        # Only set lock if multiple streams share this GPU
        if used_gpus[assigned_gpu] > 1:
            pipeline.set_model_lock(gpu_locks[assigned_gpu])
        
        t = threading.Thread(
            target=_run_pipeline_thread,
            args=(pipeline, video_source),
            name=f"stream-{stream_id}",
            daemon=True
        )
        threads.append(t)
    
    # Start all
    print(f"🚀 Launching {len(threads)} parallel streams...\n")
    for t in threads:
        t.start()
    
    # Wait for all to finish (Ctrl-C to stop)
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user — streams will stop")
    
    print("\n✅ All streams finished — shutdown complete")


def _run_pipeline_thread(pipeline: InferencePipeline, source):
    """Thread target: run one pipeline on one source."""
    try:
        pipeline.run_video(source, display=True)
    except Exception as e:
        print(f"❌ [{pipeline.stream_id}] Error: {e}")
        import traceback
        traceback.print_exc()


# ------------------------------------------------------------------ helpers

def _start_api_background():
    """Launch the Flask API server in a daemon thread."""
    print("🌐 Starting API server in background...")
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("✅ API server started\n")


def run_api_only():
    """Run API server only (no inference)."""
    settings.print_config()
    print("🌐 Starting API server only mode...")
    print("(No inference pipeline will run)\n")
    try:
        run_api_server()
    except KeyboardInterrupt:
        print("\n⏹️  API server stopped")


# ------------------------------------------------------------------ main

def main():
    """Main application entry point."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="SafeSight AI - Real-Time Safety Monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py webcam                        # Single webcam
  python app.py video.mp4                     # Single video
  python app.py v1.mp4 v2.mp4 rtsp://cam1    # Multiple sources
  python app.py webcam --with-api             # With API server
  python app.py --api-only                    # API server only
        """
    )
    
    parser.add_argument(
        'sources',
        nargs='*',
        metavar='SOURCE',
        help='Video source(s): "webcam", file path(s), or stream URL(s)'
    )
    
    parser.add_argument(
        '--api-only',
        action='store_true',
        help='Run API server only (no inference)'
    )
    
    parser.add_argument(
        '--with-api',
        action='store_true',
        help='Run API server alongside inference'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Run inference without display window'
    )
    
    args = parser.parse_args()
    
    validate_environment()
    
    if args.api_only:
        run_api_only()
    elif args.sources:
        if len(args.sources) == 1:
            run_inference(args.sources[0], with_api=args.with_api)
        else:
            run_multi_inference(args.sources, with_api=args.with_api)
    else:
        parser.print_help()
        print("\n❌ Error: Please specify a video source or use --api-only")
        sys.exit(1)


if __name__ == "__main__":
    main()

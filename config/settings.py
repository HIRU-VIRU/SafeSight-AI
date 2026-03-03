"""
Configuration settings for SafeSight AI system.
Supports environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Base paths
MODEL_PATH      = os.getenv("MODEL_PATH",      str(BASE_DIR / "model" / "best.pt"))
DATABASE_PATH   = os.getenv("DATABASE_PATH",   str(BASE_DIR / "safesight.db"))
STORAGE_PATH    = os.getenv("STORAGE_PATH",    str(BASE_DIR / "storage" / "violations"))
DEMO_STORAGE_PATH = os.getenv("DEMO_STORAGE_PATH", str(BASE_DIR / "storage" / "demo"))
LOG_PATH        = os.getenv("LOG_PATH",        str(BASE_DIR / "logs"))

# YOLO Detection Configuration
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.3"))
IMG_SIZE = int(os.getenv("IMG_SIZE", "512"))
DEVICE = os.getenv("DEVICE", "0")  # "0" for GPU, "cpu" for CPU

# Violation Detection Configuration
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.3"))

# Logging Configuration
DUPLICATE_COOLDOWN_SECONDS = int(os.getenv("DUPLICATE_COOLDOWN_SECONDS", "10"))

# Camera Configuration
CAMERA_ID = os.getenv("CAMERA_ID", "camera_01")

# Tracking Configuration
TRACKER_MAX_DISAPPEARED = int(os.getenv("TRACKER_MAX_DISAPPEARED", "150"))
TRACKER_IOU_MATCH_THRESHOLD = float(os.getenv("TRACKER_IOU_MATCH_THRESHOLD", "0.2"))
TRACKER_MAX_CENTROID_DISTANCE = float(os.getenv("TRACKER_MAX_CENTROID_DISTANCE", "150"))

# Violation Temporal Smoothing
MIN_VIOLATION_FRAMES = int(os.getenv("MIN_VIOLATION_FRAMES", "15"))
MIN_VISIBLE_HEIGHT = int(os.getenv("MIN_VISIBLE_HEIGHT", "100"))
FRAME_BOTTOM_MARGIN = int(os.getenv("FRAME_BOTTOM_MARGIN", "30"))

# Positive memory window – if PPE was detected within this many seconds,
# the person is still considered compliant even if current frame misses it.
PPE_MEMORY_WINDOW_SECONDS = float(os.getenv("PPE_MEMORY_WINDOW_SECONDS", "3.0"))

# Alert Configuration
ENABLE_SOUND_ALERT = os.getenv("ENABLE_SOUND_ALERT", "false").lower() == "true"
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", None)

# API Configuration
# Render injects $PORT at runtime; API_PORT is the local dev fallback.
API_HOST  = os.getenv("API_HOST",  "0.0.0.0")
API_PORT  = int(os.getenv("PORT") or os.getenv("API_PORT", "5000"))
API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"

# Performance Configuration
TARGET_FPS = int(os.getenv("TARGET_FPS", "20"))

# YOLO Model Classes (6 classes)
CLASS_NAMES = {
    0: "Person",
    1: "helmet",
    2: "gloves",
    3: "vest",
    4: "boots",
    5: "goggles"
}

# PPE policy – mandatory triggers CRITICAL, optional triggers WARNING
MANDATORY_PPE = ["helmet", "vest"]
OPTIONAL_PPE = ["boots", "gloves", "goggles"]
REQUIRED_PPE = MANDATORY_PPE + OPTIONAL_PPE


def validate_config() -> bool:
    """Validate configuration and check required files exist."""
    if not Path(MODEL_PATH).exists():
        print(f"❌ Model file not found: {MODEL_PATH}")
        return False
    
    # Create storage directories if they don't exist
    Path(STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path(DEMO_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    Path(LOG_PATH).mkdir(parents=True, exist_ok=True)
    
    print("✅ Configuration validated successfully")
    return True


def print_config():
    """Print current configuration."""
    print("\n" + "="*50)
    print("SafeSight AI - Configuration")
    print("="*50)
    print(f"Model Path: {MODEL_PATH}")
    print(f"Database Path: {DATABASE_PATH}")
    print(f"Storage Path: {STORAGE_PATH}")
    print(f"Log Path: {LOG_PATH}")
    print(f"Camera ID: {CAMERA_ID}")
    print(f"Confidence Threshold: {CONF_THRESHOLD}")
    print(f"IoU Threshold: {IOU_THRESHOLD}")
    print(f"Device: {DEVICE}")
    print(f"Target FPS: {TARGET_FPS}")
    print(f"Duplicate Cooldown: {DUPLICATE_COOLDOWN_SECONDS}s")
    print(f"Tracker IoU Match: {TRACKER_IOU_MATCH_THRESHOLD}")
    print(f"Tracker Max Centroid Dist: {TRACKER_MAX_CENTROID_DISTANCE}")
    print(f"Min Violation Frames: {MIN_VIOLATION_FRAMES}")
    print(f"PPE Memory Window: {PPE_MEMORY_WINDOW_SECONDS}s")
    print(f"Mandatory PPE: {MANDATORY_PPE}")
    print(f"Optional PPE: {OPTIONAL_PPE}")
    print("="*50 + "\n")

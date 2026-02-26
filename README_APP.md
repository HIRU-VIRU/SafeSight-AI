# SafeSight AI - Production-Ready Safety Monitoring System

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env if needed
nano .env
```

### Run Application

```bash
# Run with webcam
python app.py webcam

# Run with video file
python app.py path/to/video.mp4

# Run with RTSP stream
python app.py rtsp://camera_ip:port/stream

# Run with API server enabled
python app.py webcam --with-api

# Run API server only
python app.py --api-only
```

## 📋 System Architecture

```
SafeSight-AI/
│
├── app.py                    # Main application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment configuration template
│
├── model/                   # YOLO model files
│   └── best.pt             # Trained YOLOv26m model
│
├── core/                    # Core inference modules
│   ├── detector.py         # Detection parsing
│   ├── tracker.py          # Centroid-based tracking
│   ├── violation_logic.py  # PPE violation evaluation
│   └── inference.py        # Main inference pipeline
│
├── services/                # Service modules
│   ├── database.py         # SQLite database management
│   ├── storage.py          # Evidence image storage
│   ├── alert.py           # Alert management system
│   └── logger.py          # Non-blocking violation logger
│
├── api/                     # REST API
│   └── dashboard_api.py    # Flask dashboard API
│
├── config/                  # Configuration
│   └── settings.py         # Centralized settings
│
└── storage/                 # Violation evidence storage
    └── violations/
        └── YYYY-MM-DD/     # Date-based folders
```

## 🎯 Features

### ✅ Real-Time PPE Detection
- Detects 6 classes: Person, helmet, gloves, vest, boots, goggles
- YOLO26m model optimized for construction sites
- ≥20 FPS performance on GPU

### ✅ Violation Tracking
- IoU-based PPE overlap detection (configurable threshold)
- Lightweight centroid-based person tracking
- Duplicate prevention (configurable cooldown)

### ✅ Evidence Management
- Automatic violation image capture
- Date-based folder organization
- SQLite database with indexed queries

### ✅ Alert System
- Console alerts with formatted output
- Optional sound notifications
- Webhook support for external integrations

### ✅ Dashboard API
- REST API for analytics
- Endpoints: `/violations/today`, `/violations/count`, `/violations/hourly`, `/violations/export`
- CORS-enabled for frontend integration

## 🔧 Configuration

Edit `.env` file to customize:

```bash
# Detection
CONF_THRESHOLD=0.3          # Confidence threshold
IOU_THRESHOLD=0.3           # IoU threshold for PPE overlap
DEVICE=0                    # GPU device (0) or "cpu"

# Logging
DUPLICATE_COOLDOWN_SECONDS=10    # Prevent duplicate logs
CAMERA_ID=camera_01             # Camera identifier

# API
API_PORT=5000              # API server port
API_HOST=0.0.0.0          # Server host

# Alerts
ENABLE_SOUND_ALERT=false
ALERT_WEBHOOK_URL=https://your-webhook.com/alerts
```

## 📊 API Endpoints

### GET /violations/today
Get all violations from today
```bash
curl http://localhost:5000/violations/today
```

### GET /violations/count
Get violation count with optional filters
```bash
curl "http://localhost:5000/violations/count?start_date=2026-02-01&end_date=2026-02-25"
```

### GET /violations/hourly
Get hourly statistics for a date
```bash
curl "http://localhost:5000/violations/hourly?date=2026-02-25"
```

### GET /violations/export
Export violations to CSV
```bash
curl "http://localhost:5000/violations/export?start_date=2026-02-01" -o violations.csv
```

### GET /violations/stats
Get overall statistics summary
```bash
curl http://localhost:5000/violations/stats
```

## 🔬 Model Information

**YOLOv26m trained on construction PPE dataset**

Classes (6):
- 0: Person
- 1: helmet
- 2: gloves
- 3: vest
- 4: boots
- 5: goggles

Violation logic:
- For each detected Person, check if required PPE overlaps (IoU >= threshold)
- Missing PPE = Violation flagged
- Multiple simultaneous violations supported

## 🏗️ Development

### Testing Individual Components

```python
# Test detection parser
from core.detector import DetectionParser
parser = DetectionParser()

# Test tracker
from core.tracker import CentroidTracker
tracker = CentroidTracker()

# Test violation engine
from core.violation_logic import ViolationEngine
engine = ViolationEngine()

# Test database
from services.database import DatabaseService
db = DatabaseService()
```

### Code Standards
- Type hints for all functions
- Docstrings for classes and methods
- Modular, single-responsibility design
- Exception handling throughout
- Non-blocking I/O operations

## 📈 Performance

- **Target:** ≥20 FPS on GPU
- **Async logging:** Background thread prevents blocking
- **Efficient tracking:** Lightweight centroid-based algorithm
- **Optimized storage:** Date-based folder structure

## 🛠️ Troubleshooting

### Model not found
```bash
# Ensure best.pt is in model/ directory
ls model/best.pt
```

### Low FPS
- Check GPU availability: `nvidia-smi`
- Reduce IMG_SIZE in config
- Lower CONF_THRESHOLD

### Database locked
- Only one process can write at a time
- Check for zombie processes
- Restart application

## 📝 License

See LICENSE file.

## 🤝 Contributing

This is a production system for TN-IMPACT 2026.

## 📧 Contact

For issues or questions, contact the development team.

---

**SafeSight AI** - Enterprise Construction Safety Monitoring System

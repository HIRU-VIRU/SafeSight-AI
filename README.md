# SafeSight AI

**Real-Time Construction Safety Monitoring System**

SafeSight AI is a production-grade computer vision platform that detects PPE (Personal Protective Equipment) violations on construction sites in real time. It runs YOLO-based inference on live camera feeds or video files, logs every violation with photographic evidence, stores records in a database, and serves analytics through a REST API consumed by a React dashboard.

---

## Features

- Real-time multi-PPE violation detection (helmet, vest, boots, gloves, goggles)
- Centroid-based person tracker with persistent IDs across frames
- IoU-based PPE assignment per tracked person
- Duplicate-suppression cooldown prevents log spam
- Async, non-blocking violation logger (queue + background thread)
- Evidence images saved to date-organised folders
- SQLite database with CSV export
- Flask REST API for analytics
- React + Vite dashboard with Recharts visualisations
- Multi-stream support (run several cameras in parallel)
- Graceful shutdown handling

---

## Detected Classes

The YOLO26m model (`best.pt`) is trained on exactly **6 classes**:

| ID | Class   |
|----|---------|
| 0  | Person  |
| 1  | helmet  |
| 2  | gloves  |
| 3  | vest    |
| 4  | boots   |
| 5  | goggles |

A violation is inferred from the **absence** of a required PPE item overlapping a tracked Person bounding box (IoU ≥ threshold).

---

## Project Structure

```
SafeSight-AI/
├── app.py                  # Main entry point
├── requirements.txt
├── .env                    # Environment overrides (optional)
│
├── model/
│   └── best.pt             # Trained YOLO26m weights
│
├── core/
│   ├── inference.py        # Per-frame pipeline orchestration
│   ├── detector.py         # YOLO output → structured dicts
│   ├── tracker.py          # Centroid-based person tracker
│   ├── violation_logic.py  # IoU-based PPE violation engine
│   └── utils.py
│
├── services/
│   ├── logger.py           # Async violation logger (queue + thread)
│   ├── database.py         # SQLite CRUD + analytics queries
│   ├── alert.py            # Console / webhook alerts
│   └── storage.py          # Evidence image storage
│
├── api/
│   └── dashboard_api.py    # Flask REST API
│
├── config/
│   └── settings.py         # Centralised config with .env support
│
├── frontend/               # React + Vite dashboard
│   └── src/
│
└── storage/
    └── violations/         # Saved evidence images (date-organised)
```

---

## Requirements

- Python ≥ 3.10
- Node.js ≥ 18 (for the dashboard)
- CUDA-capable GPU recommended (CPU mode supported)

---

## Installation

### Backend

```bash
# Clone and enter the repo
git clone https://github.com/your-org/SafeSight-AI.git
cd SafeSight-AI

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Configuration

All settings are controlled by `config/settings.py` and can be overridden via a `.env` file in the project root.

| Variable                    | Default              | Description                                      |
|-----------------------------|----------------------|--------------------------------------------------|
| `MODEL_PATH`                | `model/best.pt`      | Path to YOLO weights                             |
| `DATABASE_PATH`             | `safesight.db`       | SQLite database path                             |
| `STORAGE_PATH`              | `storage/violations` | Root folder for evidence images                  |
| `CONF_THRESHOLD`            | `0.3`                | YOLO confidence threshold                        |
| `IOU_THRESHOLD`             | `0.3`                | IoU threshold for PPE–Person overlap             |
| `DUPLICATE_COOLDOWN_SECONDS`| `10`                 | Minimum seconds between repeated logs per person |
| `DEVICE`                    | `0`                  | `0` = first GPU, `cpu` = CPU only                |
| `CAMERA_ID`                 | `camera_01`          | Identifier embedded in log records               |
| `IMG_SIZE`                  | `512`                | YOLO inference resolution                        |
| `MIN_VIOLATION_FRAMES`      | `15`                 | Frames a violation must persist before logging   |
| `PPE_MEMORY_WINDOW_SECONDS` | `3.0`                | PPE detected in this window → still compliant    |
| `API_HOST`                  | `0.0.0.0`            | Flask bind address                               |
| `API_PORT`                  | `5000`               | Flask port                                       |
| `ENABLE_SOUND_ALERT`        | `false`              | Play terminal bell on violation                  |
| `ALERT_WEBHOOK_URL`         | *(unset)*            | POST alert payload to this URL                   |
| `TARGET_FPS`                | `20`                 | Target inference frame rate                      |

Example `.env`:

```env
DEVICE=0
CONF_THRESHOLD=0.35
DUPLICATE_COOLDOWN_SECONDS=15
ALERT_WEBHOOK_URL=https://hooks.example.com/safesight
```

---

## Usage

### Run inference on a video file

```bash
python app.py path/to/video.mp4
```

### Run inference on a webcam

```bash
python app.py webcam
# or by index
python app.py 0
```

### Run inference on an RTSP stream

```bash
python app.py rtsp://192.168.1.10:554/stream
```

### Run multiple sources in parallel

```bash
python app.py video1.mp4 video2.mp4 rtsp://cam1
```

### Run the API server only (no inference)

```bash
python app.py --api-only
```

### Run inference and the API server together

```bash
python app.py webcam --with-api
```

---

## Dashboard

Start the React development server:

```bash
cd frontend
npm run dev
```

The dashboard is accessible at `http://localhost:5173` and connects to the Flask API at `http://localhost:5000`.

To build for production:

```bash
cd frontend
npm run build
```

---

## REST API Reference

Base URL: `http://localhost:5000`

| Method | Endpoint                         | Description                              |
|--------|----------------------------------|------------------------------------------|
| GET    | `/`                              | Service info and endpoint list           |
| GET    | `/health`                        | Health check                             |
| GET    | `/violations/today`              | All violations logged today              |
| GET    | `/violations/recent`             | Most recent N violations                 |
| GET    | `/violations/count`              | Total violation count (with filters)     |
| GET    | `/violations/hourly`             | Hourly breakdown for the last 24 h       |
| GET    | `/violations/stats`              | Aggregate statistics                     |
| GET    | `/violations/filter`             | Filtered violations by date / camera     |
| GET    | `/violations/severity-counts`    | Count by PPE type                        |
| GET    | `/violations/cameras`            | List all camera IDs in DB                |
| GET    | `/violations/dates`              | List all dates that have records         |
| GET    | `/violations/export`             | Download violations as CSV               |
| GET    | `/violations/image/<path>`       | Serve a saved evidence image             |
| POST   | `/inference/start`               | Start an inference stream via API        |
| GET    | `/inference/status`              | Status of all running inference streams  |
| POST   | `/inference/stop`                | Stop an inference stream                 |
| GET    | `/inference/stream/<stream_id>`  | MJPEG live feed for a running stream     |

---

## Database Schema

```sql
CREATE TABLE violations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT,
    camera_id         TEXT,
    person_id         INTEGER,
    helmet_violation  INTEGER,
    vest_violation    INTEGER,
    boots_violation   INTEGER,
    gloves_violation  INTEGER,
    goggles_violation INTEGER,
    image_path        TEXT
);
```

---

## Evidence Storage

Violation images are saved to:

```
storage/violations/YYYY-MM-DD/
    camera1_2026-02-25_15-34-22_person3.jpg
```

---

## Performance

- Target: **≥ 20 FPS** on a mid-range GPU
- All disk I/O (image save + DB insert) happens on a **background thread**
- No blocking operations inside the main inference loop
- Duplicate suppression reduces unnecessary writes

---

## License

See [LICENSE](LICENSE).

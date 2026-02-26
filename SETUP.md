# SafeSight AI - Installation & Setup Guide

## Prerequisites

- Python 3.8 or higher
- GPU with CUDA support (recommended) or CPU
- Webcam or video source for testing

## Step-by-Step Installation

### 1. Clone or Navigate to Repository

```bash
cd SafeSight-AI
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Note:** This will install:
- PyTorch and torchvision
- Ultralytics (YOLO)
- OpenCV
- Flask and Flask-CORS
- NumPy, SciPy
- Other utilities

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration if needed
nano .env  # or use your preferred editor
```

### 5. Verify Model File

Ensure the trained YOLO model is in place:

```bash
ls -lh model/best.pt
```

If the model file is missing, copy your trained `best.pt` to the `model/` directory.

### 6. Test Installation

```bash
# Test with help command
python app.py --help

# Quick validation (will check model and config)
python app.py --api-only
# Press Ctrl+C after you see "Running on http://..."
```

## Quick Test Run

### Option 1: Test with Webcam

```bash
python app.py webcam
```

Press 'q' to quit the video window.

### Option 2: Test with Video File

```bash
# Use your own video file
python app.py path/to/your/video.mp4
```

### Option 3: Test API Server

```bash
# Start API server
python app.py --api-only
```

Then open browser to `http://localhost:5000` or test with curl:

```bash
curl http://localhost:5000/
curl http://localhost:5000/violations/stats
```

## Troubleshooting

### Issue: "Model file not found"

**Solution:**
```bash
# Check if model exists
ls model/best.pt

# If missing, copy your trained model
cp /path/to/your/best.pt model/
```

### Issue: "Import error" or "Module not found"

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "CUDA not available" or slow performance

**Solution:**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, edit .env to use CPU
echo "DEVICE=cpu" >> .env
```

**Note:** CPU mode will be slower (~5-10 FPS vs 20+ FPS on GPU)

### Issue: "Database is locked"

**Solution:**
```bash
# Stop all running instances
pkill -f "python app.py"

# Remove database file and restart
rm safesight.db
python app.py webcam
```

### Issue: Low FPS (< 10 FPS)

**Solutions:**
1. Lower image size:
   ```bash
   echo "IMG_SIZE=416" >> .env
   ```

2. Increase confidence threshold (fewer detections):
   ```bash
   echo "CONF_THRESHOLD=0.5" >> .env
   ```

3. Use GPU if available

## Production Deployment

### Run as Background Service

Create systemd service file (Linux):

```bash
sudo nano /etc/systemd/system/safesight.service
```

```ini
[Unit]
Description=SafeSight AI Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/SafeSight-AI
ExecStart=/path/to/SafeSight-AI/venv/bin/python app.py rtsp://camera/stream --with-api
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable safesight
sudo systemctl start safesight
sudo systemctl status safesight
```

### Monitor Logs

```bash
# View real-time logs
sudo journalctl -u safesight -f
```

## Advanced Configuration

### Custom IoU Threshold

For stricter PPE detection (PPE must overlap more with person):
```bash
echo "IOU_THRESHOLD=0.5" >> .env
```

For more lenient detection:
```bash
echo "IOU_THRESHOLD=0.2" >> .env
```

### Duplicate Cooldown

Adjust how long to wait before logging same person again (seconds):
```bash
echo "DUPLICATE_COOLDOWN_SECONDS=30" >> .env
```

### Enable Webhooks

Send alerts to external system:
```bash
echo "ALERT_WEBHOOK_URL=https://your-webhook.com/alerts" >> .env
```

### Change API Port

```bash
echo "API_PORT=8080" >> .env
```

## Accessing the System

### View Violations Database

```bash
# Install SQLite viewer
sudo apt install sqlitebrowser  # Linux
# or
brew install --cask db-browser-for-sqlite  # Mac

# Open database
sqlitebrowser safesight.db
```

### Export Violations

```bash
curl "http://localhost:5000/violations/export" -o violations.csv
```

### View Stored Images

```bash
# Navigate to storage
cd storage/violations

# List today's violations
ls -lh $(date +%Y-%m-%d)/
```

## Performance Benchmarks

**Expected Performance:**

| Hardware | FPS | Notes |
|----------|-----|-------|
| NVIDIA RTX 3060+ | 20-30 | Recommended |
| NVIDIA GTX 1060+ | 15-20 | Good |
| Intel i7 CPU | 5-8 | Acceptable |
| Intel i5 CPU | 3-5 | Minimal |

## Next Steps

1. ✅ Test with sample video
2. ✅ Configure for your camera source
3. ✅ Test violation detection accuracy
4. ✅ Adjust thresholds if needed
5. ✅ Set up as system service for production
6. ✅ Integrate dashboard API with frontend (if needed)

## Support

For issues, check:
1. Model file exists: `ls model/best.pt`
2. Dependencies installed: `pip list`
3. Configuration file: `cat .env`
4. System logs: `tail -f *.log`

---

**SafeSight AI** - Ready for Production Deployment

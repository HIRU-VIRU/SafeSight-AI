# SafeSight AI - Quick Start Guide

## ⚡ Get Up and Running in 5 Minutes

### 1. Install Dependencies (2 minutes)

```bash
# Install Python packages
pip install -r requirements.txt
```

### 2. Verify Installation (30 seconds)

```bash
# Run system test
python test_system.py
```

Expected output:
```
✅ All modules imported successfully
✅ Configuration validated
✅ Database operations successful
✅ Storage service working
✅ Alert system working
✅ Tracker working
✅ Violation engine working
✅ Model found
✅ All dependencies installed

🎉 System is ready for inference!
```

### 3. Run Your First Inference (2 minutes)

#### Option A: Webcam
```bash
python app.py webcam
```

#### Option B: Video File
```bash
python app.py path/to/your/video.mp4
```

#### Option C: RTSP Stream
```bash
python app.py rtsp://camera_ip:port/stream
```

**Press 'q' to quit the video window**

---

## 🎯 What You'll See

### Live Video Window
- **Green boxes** = Person with all required PPE ✅
- **Red boxes** = Person with missing PPE ❌
- **Yellow boxes** = Detected PPE items
- **Person ID** = Unique tracker ID for each person
- **Missing PPE list** = Shown below violation boxes

### Console Output
```
⚠️ PPE VIOLATION DETECTED
Camera: camera_01
Time: 15:34:22
Person ID: 3
Violations: helmet, boots
```

### Saved Evidence
- Images saved to: `storage/violations/YYYY-MM-DD/`
- Format: `camera_01_2026-02-25_15-34-22_person3.jpg`

### Database
- Violations logged to: `safesight.db`
- View with: `sqlite3 safesight.db`

---

## 🔧 Optional: Configure Settings

```bash
# Copy example config
cp .env.example .env

# Edit settings
nano .env
```

**Key settings:**
- `CONF_THRESHOLD=0.3` - Detection confidence (higher = fewer detections)
- `IOU_THRESHOLD=0.3` - PPE overlap threshold (higher = stricter)
- `DUPLICATE_COOLDOWN_SECONDS=10` - Seconds between same person logs
- `CAMERA_ID=camera_01` - Your camera identifier

---

## 🌐 Optional: Run with API Server

```bash
# Run inference + API server
python app.py webcam --with-api
```

Then access API at: http://localhost:5000

**Try these endpoints:**
```bash
# Get today's violations
curl http://localhost:5000/violations/today

# Get statistics
curl http://localhost:5000/violations/stats

# Export to CSV
curl http://localhost:5000/violations/export -o violations.csv
```

---

## 🚨 Troubleshooting

### "Model file not found"
```bash
# Ensure best.pt is in model/ directory
ls model/best.pt
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Low FPS (< 10)
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, use CPU mode (edit .env)
echo "DEVICE=cpu" >> .env
```

### "Database is locked"
```bash
# Stop all instances
pkill -f "python app.py"

# Remove DB and restart
rm safesight.db
python app.py webcam
```

---

## 📊 View Your Data

### Database Queries
```bash
# Open database
sqlite3 safesight.db

# View all violations
SELECT * FROM violations;

# Count today's violations
SELECT COUNT(*) FROM violations 
WHERE date(timestamp) = date('now');
```

### View Saved Images
```bash
# Navigate to today's folder
cd storage/violations/$(date +%Y-%m-%d)

# View images
ls -lh
```

---

## ✅ That's It!

You now have a fully functional real-time PPE violation detection system running.

**Next steps:**
- Adjust thresholds in `.env` for your use case
- Integrate API with your dashboard
- Deploy as a service (see SETUP.md)
- Connect to your RTSP cameras

---

## 📞 Need Help?

1. Check `SETUP.md` for detailed installation
2. Check `README_APP.md` for complete documentation
3. Run `python test_system.py` to diagnose issues
4. Check `IMPLEMENTATION_SUMMARY.md` for architecture details

---

**SafeSight AI** - Built for TN-IMPACT 2026

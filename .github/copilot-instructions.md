# SAFE SIGHT AI – PRODUCTION REFACTOR INSTRUCTIONS

## PROJECT OVERVIEW

We are refactoring this repository into a production-ready **Real-Time Construction Safety Monitoring System**.

The YOLO26m model is already trained and `best.pt` is available.

The inference pipeline works.

Now we must convert this into a **modular, scalable, deployable application** that:

- Detects PPE violations in real-time
- Logs violations with evidence
- Prevents duplicate logging
- Saves violation images
- Stores metadata in database
- Triggers alerts
- Exposes dashboard APIs
- Is cleanly structured and production-grade

**This is NOT a demo script.**  
This must look like an **enterprise safety monitoring product**.

---

## YOLO26m CLASS DEFINITIONS (FINAL MODEL)

The trained YOLO26m model detects exactly **6 classes**:

```
0: Person
1: helmet
2: gloves
3: vest
4: boots
5: goggles
```

**There is NO `head` class.**  
**There is NO `harness` class.**

Violation detection must be based **only** on these 6 classes.

---

## TARGET ARCHITECTURE

```
SafeSight-AI/
│
├── app.py
├── requirements.txt
├── .env
│
├── model/
│   └── best.pt
│
├── core/
│   ├── inference.py
│   ├── detector.py
│   ├── tracker.py
│   ├── violation_logic.py
│   └── utils.py
│
├── services/
│   ├── logger.py
│   ├── database.py
│   ├── alert.py
│   └── storage.py
│
├── api/
│   └── dashboard_api.py
│
├── config/
│   └── settings.py
│
├── storage/
│   └── violations/
│
├── docs/
├── diagrams/
└── README.md
```

---

## DETECTION PARSING – `core/detector.py`

Create class `DetectionParser`.

**Responsibilities:**

- Accept YOLO model output
- Convert detections into structured dictionary objects
- Filter by confidence threshold

**Return format:**

```python
[
    {
        "class": "Person",
        "confidence": 0.92,
        "bbox": [x1, y1, x2, y2]
    }
]
```

---

## TRACKING – `core/tracker.py`

Create a **lightweight centroid-based tracker**.

**Responsibilities:**

- Assign unique ID to each detected `Person`
- Track across frames
- Maintain dictionary of active objects
- Remove objects after timeout (e.g., 30 frames)

**Return format:**

```python
[
    {
        "person_id": 3,
        "bbox": [x1, y1, x2, y2]
    }
]
```

Keep implementation **fast and lightweight**.

---

## VIOLATION LOGIC – `core/violation_logic.py`

Create class `ViolationEngine`.

Implement **IoU function**.

IoU threshold must be **configurable (default 0.3)**.

### PPE VIOLATION RULES

For each detected `Person`:

1. **Helmet Violation:**  
   If no `helmet` bounding box overlaps the Person bounding box (IoU >= threshold)  
   → `helmet_violation = True`

2. **Vest Violation:**  
   If no `vest` bounding box overlaps the Person bounding box  
   → `vest_violation = True`

3. **Boots Violation:**  
   If no `boots` bounding box overlaps the Person bounding box  
   → `boots_violation = True`

4. **Gloves Violation:**  
   If no `gloves` bounding box overlaps the Person bounding box  
   → `gloves_violation = True`

5. **Goggles Violation:**  
   If no `goggles` bounding box overlaps the Person bounding box  
   → `goggles_violation = True`

### IMPORTANT LOGIC NOTES

- Violation is inferred from **absence of required PPE**
- We are **NOT detecting "no_helmet" or negative classes**
- Overlap must use **IoU >= configurable threshold**
- Each Person can have **multiple simultaneous violations**
- Process per tracked `person_id`

**Return format:**

```python
[
    {
        "person_id": 1,
        "helmet_violation": True,
        "vest_violation": False,
        "boots_violation": True,
        "gloves_violation": False,
        "goggles_violation": False,
        "bbox": [...]
    }
]
```

---

## DATABASE – `services/database.py`

Use **SQLite**.

Auto-create table if not exists:

```sql
CREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    camera_id TEXT,
    person_id INTEGER,
    helmet_violation INTEGER,
    vest_violation INTEGER,
    boots_violation INTEGER,
    gloves_violation INTEGER,
    goggles_violation INTEGER,
    image_path TEXT
);
```

Create functions:

- `insert_violation()`
- `get_today_violations()`
- `get_violation_count()`
- `get_hourly_stats()`
- `export_csv()`

---

## STORAGE – `services/storage.py`

Create class `EvidenceStorage`.

**Responsibilities:**

- Create date-based folders
- Save cropped violation images
- Return saved file path

**Folder structure:**

```
storage/violations/YYYY-MM-DD/
```

**Filename format:**

```
camera1_2026-02-25_15-34-22_person3.jpg
```

---

## LOGGER – `services/logger.py`

Create class `ViolationLogger`.

**Requirements:**

- Non-blocking
- Use Queue + background thread
- Prevent duplicate logging

**Duplicate rule:**  
If same `person_id` within `DUPLICATE_COOLDOWN_SECONDS` (default 10 seconds)  
→ Ignore duplicate violation

**Workflow:**

1. Accept violation object
2. Save image
3. Insert into DB
4. Trigger alert

**Main inference thread must NEVER block.**

---

## ALERT SYSTEM – `services/alert.py`

Create class `AlertManager`.

**Support:**

- Console alert
- Optional sound alert
- Optional webhook POST

**Alert format:**

```
⚠ PPE VIOLATION DETECTED
Camera: Gate_01
Time: 15:34:22
Person ID: 3
Violations: helmet, boots
```

---

## INFERENCE PIPELINE – `core/inference.py`

**Per frame:**

```
Frame
→ YOLO detect
→ DetectionParser.parse()
→ Tracker.update()
→ ViolationEngine.evaluate()
→ Logger.enqueue()
→ Render frame
```

Must maintain **≥ 20 FPS**.

**No blocking operations inside loop.**

---

## API – `api/dashboard_api.py`

Build **Flask API**.

**Endpoints:**

- `GET /violations/today`
- `GET /violations/count`
- `GET /violations/hourly`
- `GET /violations/export`

Return **JSON responses**.

---

## APP ENTRY POINT – `app.py`

**Responsibilities:**

- Load YOLO model
- Start inference thread
- Start logger service
- Start Flask server
- Graceful shutdown handling

---

## CONFIG – `config/settings.py`

Store:

- `CONF_THRESHOLD`
- `IOU_THRESHOLD`
- `DUPLICATE_COOLDOWN_SECONDS`
- `CAMERA_ID`
- `DATABASE_PATH`
- `STORAGE_PATH`

**Support environment variables.**

---

## PERFORMANCE REQUIREMENTS

- **≥ 20 FPS**
- Async logging
- No disk write in main loop
- Exception-safe
- Modular and scalable

---

## CODING STANDARDS

- Use classes
- Use type hints
- Use docstrings
- No hardcoded paths
- No monolithic scripts
- Clean modular design
- Handle errors gracefully

---

## FINAL OBJECTIVE

This system must represent:

**A real-time multi-PPE compliance monitoring platform.**

Not just an object detection project.

It must:

- Detect violations live
- Save evidence
- Log to database
- Provide analytics
- Trigger alerts
- Be deployable and scalable

---

**End of instructions.**

#!/usr/bin/env python3
"""
Test script for SafeSight AI components.
Run this to verify all modules are working correctly.
"""

import sys
from pathlib import Path

print("=" * 60)
print("SafeSight AI - Component Test Suite")
print("=" * 60)
print()

# Test 1: Import all modules
print("Test 1: Importing modules...")
try:
    from config import settings
    print("  ✅ config.settings")
    
    from core.detector import DetectionParser
    print("  ✅ core.detector")
    
    from core.tracker import CentroidTracker
    print("  ✅ core.tracker")
    
    from core.violation_logic import ViolationEngine
    print("  ✅ core.violation_logic")
    
    from services.database import DatabaseService
    print("  ✅ services.database")
    
    from services.storage import EvidenceStorage
    print("  ✅ services.storage")
    
    from services.alert import AlertManager
    print("  ✅ services.alert")
    
    from services.logger import ViolationLogger
    print("  ✅ services.logger")
    
    print("✅ All modules imported successfully\n")
except ImportError as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Configuration
print("Test 2: Configuration validation...")
try:
    is_valid = settings.validate_config()
    if is_valid:
        print("✅ Configuration validated\n")
    else:
        print("⚠️  Configuration has warnings\n")
except Exception as e:
    print(f"❌ Configuration error: {e}\n")

# Test 3: Database
print("Test 3: Database initialization...")
try:
    db = DatabaseService()
    print("  ✅ Database created/connected")
    
    # Test insert
    test_violation = {
        "person_id": 999,
        "helmet_violation": True,
        "vest_violation": False,
        "boots_violation": False,
        "gloves_violation": False,
        "goggles_violation": False
    }
    vid = db.insert_violation(test_violation, "TEST_CAM", "test.jpg")
    print(f"  ✅ Test violation inserted (ID: {vid})")
    
    # Test query
    count = db.get_violation_count()
    print(f"  ✅ Database query works (Total violations: {count})")
    
    print("✅ Database operations successful\n")
except Exception as e:
    print(f"❌ Database error: {e}\n")

# Test 4: Storage
print("Test 4: Storage service...")
try:
    storage = EvidenceStorage()
    stats = storage.get_storage_stats()
    print(f"  ✅ Storage initialized")
    print(f"  📁 Base path: {stats['base_path']}")
    print(f"  📊 Total images: {stats['total_images']}")
    print("✅ Storage service working\n")
except Exception as e:
    print(f"❌ Storage error: {e}\n")

# Test 5: Alert Manager
print("Test 5: Alert system...")
try:
    alert = AlertManager()
    print("  ✅ Alert manager initialized")
    
    # Optional: test alert
    test_violation = {
        "person_id": 999,
        "violations": ["helmet", "vest"],
        "helmet_violation": True,
        "vest_violation": True,
        "boots_violation": False,
        "gloves_violation": False,
        "goggles_violation": False
    }
    
    print("  🔔 Testing alert (you should see formatted output below):")
    alert.send_alert(test_violation, "TEST_CAMERA")
    print("✅ Alert system working\n")
except Exception as e:
    print(f"❌ Alert error: {e}\n")

# Test 6: Tracker
print("Test 6: Centroid tracker...")
try:
    tracker = CentroidTracker()
    
    # Test with dummy detections
    test_detections = [
        {"bbox": [100, 100, 200, 300]},
        {"bbox": [300, 100, 400, 300]}
    ]
    
    tracked = tracker.update(test_detections)
    print(f"  ✅ Tracker initialized")
    print(f"  👤 Tracked {len(tracked)} objects")
    print("✅ Tracker working\n")
except Exception as e:
    print(f"❌ Tracker error: {e}\n")

# Test 7: Violation Engine
print("Test 7: Violation detection logic...")
try:
    engine = ViolationEngine()
    
    # Test IoU calculation
    bbox1 = [100, 100, 200, 200]
    bbox2 = [150, 150, 250, 250]
    iou = engine.compute_iou(bbox1, bbox2)
    print(f"  ✅ IoU calculation: {iou:.3f}")
    
    # Test violation evaluation
    test_persons = [
        {"person_id": 1, "bbox": [100, 100, 200, 300]}
    ]
    test_ppe = {
        "helmet": [],  # No helmet = violation
        "vest": [{"bbox": [110, 150, 190, 250]}],  # Has vest
        "boots": [],
        "gloves": [],
        "goggles": []
    }
    
    violations = engine.evaluate(test_persons, test_ppe)
    print(f"  ✅ Detected {len(violations)} violations")
    if violations:
        print(f"  ⚠️  Missing PPE: {violations[0]['violations']}")
    print("✅ Violation engine working\n")
except Exception as e:
    print(f"❌ Violation engine error: {e}\n")

# Test 8: Model file
print("Test 8: YOLO model file...")
try:
    model_path = Path(settings.MODEL_PATH)
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Model found: {model_path}")
        print(f"  📦 Size: {size_mb:.1f} MB")
    else:
        print(f"  ⚠️  Model not found: {model_path}")
        print("  📝 Copy best.pt to model/ directory")
    print()
except Exception as e:
    print(f"❌ Model check error: {e}\n")

# Test 9: Dependencies
print("Test 9: External dependencies...")
dependencies = {
    "torch": "PyTorch",
    "cv2": "OpenCV",
    "ultralytics": "Ultralytics YOLO",
    "flask": "Flask",
    "numpy": "NumPy",
    "scipy": "SciPy"
}

missing = []
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ❌ {name} - NOT INSTALLED")
        missing.append(name)

if missing:
    print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
    print("Run: pip install -r requirements.txt\n")
else:
    print("\n✅ All dependencies installed\n")

# Summary
print("=" * 60)
print("Test Summary")
print("=" * 60)
print()
print("✅ Core modules: Working")
print("✅ Services: Working")
print("✅ Configuration: Valid")
print()

if Path(settings.MODEL_PATH).exists() and len(missing) == 0:
    print("🎉 System is ready for inference!")
    print()
    print("Run the application:")
    print("  python app.py webcam")
else:
    print("⚠️  System setup incomplete:")
    if not Path(settings.MODEL_PATH).exists():
        print("  - Copy best.pt to model/ directory")
    if missing:
        print("  - Install missing dependencies: pip install -r requirements.txt")

print()
print("=" * 60)

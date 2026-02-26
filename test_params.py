#!/usr/bin/env python3
"""Test different YOLO parameter combinations"""

import cv2
from ultralytics import YOLO

print("Loading model...")
model = YOLO("model/best.pt")

print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

print("\nTesting 3 parameter combinations on first 30 frames:\n")

test_configs = [
    {"name": "Test 1: Basic (like test_detection.py)", "params": {"conf": 0.2, "verbose": False}},
    {"name": "Test 2: With imgsize=512", "params": {"conf": 0.2, "imgsz": 512, "verbose": False}},
    {"name": "Test 3: With GPU + half", "params": {"conf": 0.2, "device": 0, "half": True, "verbose": False}},
]

for config in test_configs:
    print(f"\n{'='*60}")
    print(config["name"])
    print("="*60)
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset
    detections = 0
    
    for i in range(30):
        ret, frame = cap.read()
        if not ret:
            cap.release()
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if not ret:
                break
        
        results = model(frame, **config["params"])
        
        if len(results) > 0 and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                cls = int(box.cls[0])
                if cls == 0:  # Person class
                    detections += 1
                    conf = float(box.conf[0])
                    print(f"  Frame {i+1}: Person detected (conf={conf:.3f})")
                    break
    
    print(f"\nResult: {detections}/30 frames with person detection")

cap.release()
print("\n" + "="*60)
print("Test complete")
print("="*60)

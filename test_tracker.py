#!/usr/bin/env python3
"""Test the tracker component"""

import cv2
from ultralytics import YOLO
from config import settings
from core.detector import DetectionParser
from core.tracker import CentroidTracker

print("Loading model...")
model = YOLO(settings.MODEL_PATH)

print("Initializing components...")
detector = DetectionParser(conf_threshold=0.2)
tracker = CentroidTracker()

print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

print("\nRunning detection + tracking test (30 frames):\n")

for i in range(30):
    ret, frame = cap.read()
    if not ret:
        break
    
    # YOLO detection
    results = model(
        frame,
        imgsz=512,
        conf=0.2,
        verbose=False
    )
    
    # Parse detections
    detections = detector.parse(results)
    persons = detector.get_persons(detections)
    
    # Track persons
    tracked_persons = tracker.update(persons)
    
    print(f"Frame {i+1}: Detections={len(detections)}, Persons={len(persons)}, Tracked={len(tracked_persons)}")
    
    if len(persons) > 0:
        for p in persons:
            print(f"  - Person detected: conf={p['confidence']:.3f}, bbox={[int(x) for x in p['bbox']]}")
    
    if len(tracked_persons) > 0:
        for t in tracked_persons:
            print(f"  - Tracked ID={t['person_id']}, bbox={[int(x) for x in t['bbox']]}")

cap.release()
print("\nTest complete")

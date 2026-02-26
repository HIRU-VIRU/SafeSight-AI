#!/usr/bin/env python3
"""Test detection pipeline step by step"""

import cv2
from ultralytics import YOLO
from config import settings
from core.detector import DetectionParser

print("="*60)
print("Detection Pipeline Diagnostic Test")
print("="*60)
print(f"CONF_THRESHOLD from settings: {settings.CONF_THRESHOLD}")
print(f"IMG_SIZE from settings: {settings.IMG_SIZE}")
print(f"DEVICE from settings: {settings.DEVICE}")
print("="*60)

# Load model
print("\nLoading model...")
model = YOLO(settings.MODEL_PATH)

# Initialize detector
print("Initializing DetectionParser...")
detector = DetectionParser(conf_threshold=settings.CONF_THRESHOLD)
print(f"Detector confidence threshold: {detector.conf_threshold}")

# Open webcam
print("\nOpening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

print("\nPress 'q' to quit")
print("="*60 + "\n")

frame_count = 0
detection_count = 0

while frame_count < 100:  # Test 100 frames
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    
    # YOLO detection (mimicking inference.py)
    results = model(
        frame,
        imgsz=settings.IMG_SIZE,
        conf=settings.CONF_THRESHOLD,
        device=settings.DEVICE,
        half=True if settings.DEVICE != "cpu" else False,
        verbose=False
    )
    
    # Parse detections
    detections = detector.parse(results)
    
    # Count persons
    persons = [d for d in detections if d["class"] == "Person"]
    
    if persons:
        detection_count += 1
        print(f"Frame {frame_count}: Detected {len(persons)} person(s)")
        for p in persons:
            print(f"  - Confidence: {p['confidence']:.3f}")
    
    # Show frame
    if len(results) > 0:
        annotated = results[0].plot()
        cv2.imshow("Detection Test", annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\n" + "="*60)
print(f"Total frames processed: {frame_count}")
print(f"Frames with person detections: {detection_count}")
print("="*60)

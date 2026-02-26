#!/usr/bin/env python3
"""Quick test to see what the model detects"""

import cv2
from ultralytics import YOLO

print("Loading model...")
model = YOLO("model/best.pt")

print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam")
    exit()

print("Press 'q' to quit\n")
print("="*60)

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run detection with very low confidence
    results = model(frame, conf=0.1, verbose=False)
    
    # Print raw detections
    if len(results) > 0 and len(results[0].boxes) > 0:
        frame_count += 1
        print(f"\nFrame {frame_count}:")
        for box in results[0].boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_names = {0: "Person", 1: "helmet", 2: "gloves", 3: "vest", 4: "boots", 5: "goggles"}
            class_name = class_names.get(cls, f"Class_{cls}")
            print(f"  Detected: {class_name} (confidence: {conf:.3f})")
    
    # Show annotated frame
    annotated = results[0].plot()
    cv2.imshow("Raw Detection Test (conf=0.1)", annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"\n{'='*60}")
print(f"Total frames with detections: {frame_count}")

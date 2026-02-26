#!/usr/bin/env python3
"""Test if device parameter is the issue"""

import cv2
import torch
from ultralytics import YOLO

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}\n")

model = YOLO("model/best.pt")

# Try moving model to device
device = 0 if torch.cuda.is_available() else "cpu"
print(f"Moving model to device: {device}")
model.to(device)
print("Model moved\n")

cap = cv2.VideoCapture(0)

print("Testing 5 frames with device=0 and half=True (like InferencePipeline):\n")

for i in range(5):
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model(
        frame,
        imgsz=512,
        conf=0.2,
        device=device,
        half=True if device != "cpu" else False,
        verbose=False
    )
    
    detections = len(results[0].boxes) if len(results) > 0 else 0
    persons = sum(1 for box in results[0].boxes if int(box.cls[0]) == 0) if detections > 0 else 0
    
    print(f"Frame {i+1}: detections={detections}, persons={persons}")

cap.release()
print("\nTest complete")

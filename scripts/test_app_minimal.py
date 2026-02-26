#!/usr/bin/env python3
"""Minimal app.py reproduction to debug"""

import sys
from pathlib import Path
import config.settings as settings
from core.inference import InferencePipeline

print("\n" + "="*60)
print("SAFESIGHT AI - DEBUG TEST")
print("="*60 + "\n")

# Print configuration (like app.py does)
print("Calling settings.print_config()...")
settings.print_config()

print("\nInitializing InferencePipeline...")
pipeline = InferencePipeline()

print("\nStarting logger...")
pipeline.start_logger()

print("\nOpening webcam (0)...")
import cv2
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open webcam")
    sys.exit(1)

print("✅ Webcam opened")
print("\nProcessing 10 frames...\n")

for i in range(10):
    ret, frame = cap.read()
    if not ret:
        break
    
    annotated_frame, stats = pipeline.process_frame(frame)
    
    print(f"Frame {i+1}: {stats}")
    
    #cv2.imshow("SafeSight AI - Debug", annotated_frame)
    #if cv2.waitKey(1) & 0xFF == ord('q'):
    #    break

cap.release()
cv2.destroyAllWindows()

print("\nStopping logger...")
pipeline.stop_logger()

print("\n" + "="*60)
print("DEBUG TEST COMPLETE")
print("="*60)

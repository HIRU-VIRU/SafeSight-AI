import cv2
import torch
import sys
import os
from ultralytics import YOLO

MODEL_PATH = "best.pt"
IMG_SIZE = 512
CONF_THRES = 0.3

device = 0 if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

model = YOLO(MODEL_PATH)
model.to(device)

if len(sys.argv) < 2:
    print("Usage:")
    print("  python infer.py webcam")
    print("  python infer.py video.mp4")
    print("  python infer.py http://...")
    print("  python infer.py rtsp://...")
    sys.exit()

source_input = sys.argv[1]

# 🔥 SOURCE LOGIC FIXED HERE

if source_input.lower() == "webcam":
    source = 0

elif source_input.startswith("http://") or source_input.startswith("https://"):
    source = source_input

elif source_input.startswith("rtsp://"):
    source = source_input

else:
    if not os.path.exists(source_input):
        print("File not found.")
        sys.exit()
    source = source_input


cap = cv2.VideoCapture(source)

if not cap.isOpened():
    print("Error opening stream")
    sys.exit()

print("Stream started... Press Q to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(
        frame,
        imgsz=IMG_SIZE,
        conf=CONF_THRES,
        device=device,
        half=True if device != "cpu" else False,
    )

    annotated = results[0].plot()
    cv2.imshow("TN_IMPACT - Live", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

"""
SafeSight AI – HuggingFace Space Inference API (FastAPI + Docker SDK)
YOLO26m PPE detection endpoint.

POST /infer
  Body : {"image": "<base64-jpeg>", "conf": 0.3, "imgsz": 512}
  Reply: {"detections": [...], "inference_ms": 45.2}

GET /health
  Reply: {"status": "ok", "model_loaded": true}

Classes: 0=Person, 1=helmet, 2=gloves, 3=vest, 4=boots, 5=goggles
"""

import base64
import os
import time
from typing import List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ultralytics import YOLO

# ──────────────────────────── App & model setup ───────────────────────────────

app = FastAPI(
    title="SafeSight AI Inference",
    description="YOLO26m PPE detection for construction site safety monitoring",
    version="1.0.0",
)

MODEL_PATH    = os.getenv("MODEL_PATH", "best.pt")
CONF_DEFAULT  = float(os.getenv("CONF_THRESHOLD", "0.3"))
IMGSZ_DEFAULT = int(os.getenv("IMG_SIZE", "512"))

model: Optional[YOLO] = None


@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        print(f"⚠️  Model not found at '{MODEL_PATH}'. Upload best.pt and restart.")
        return
    print(f"📦 Loading YOLO26m from '{MODEL_PATH}' ...")
    model = YOLO(MODEL_PATH)
    dummy = np.zeros((IMGSZ_DEFAULT, IMGSZ_DEFAULT, 3), dtype=np.uint8)
    model(dummy, imgsz=IMGSZ_DEFAULT, conf=CONF_DEFAULT, verbose=False)
    print("✅ Model ready")


# ──────────────────────────── Schemas ─────────────────────────────────────────

class InferRequest(BaseModel):
    image: str                  # base64-encoded JPEG
    conf:  float = CONF_DEFAULT
    imgsz: int   = IMGSZ_DEFAULT


class InferResponse(BaseModel):
    detections:   List[dict]
    inference_ms: float


# ──────────────────────────── Endpoints ───────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "SafeSight AI Inference",
        "model_loaded": model is not None,
        "endpoints": {"health": "/health", "infer": "POST /infer"},
    }


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    if model is None:
        raise HTTPException(503, detail="Model not loaded. Upload best.pt and restart.")

    try:
        img_arr = np.frombuffer(base64.b64decode(req.image), np.uint8)
        frame   = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("imdecode returned None")
    except Exception as exc:
        raise HTTPException(400, detail=f"Invalid image: {exc}")

    t0           = time.perf_counter()
    results      = model(frame, imgsz=req.imgsz, conf=req.conf, verbose=False)
    inference_ms = round((time.perf_counter() - t0) * 1000, 2)

    detections: List[dict] = []
    if results and results[0].boxes is not None:
        for box in results[0].boxes:
            detections.append({
                "class":      results[0].names[int(box.cls[0])],
                "confidence": round(float(box.conf[0]), 4),
                "bbox":       [round(v, 2) for v in box.xyxy[0].tolist()],
            })

    return InferResponse(detections=detections, inference_ms=inference_ms)

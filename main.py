import io
import os
import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

import torch
import torch.serialization

# --- PyTorch 2.6 Workaround for YOLO Model Loading ---
_original_torch_load = torch.load
def _safe_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _safe_torch_load
# -----------------------------------------------------

app = FastAPI(title="SafeStride AI Backend")

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
# This will use the model in the current folder, or download it if not present.
MODEL_PATH = "yolov8m.pt"
CONFIDENCE_THRESHOLD = 0.45

# Load model
print(f"Loading model from {MODEL_PATH}...")
model = YOLO(MODEL_PATH)

# Add CORS to allow mobile app connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
#  DETECTION LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def get_direction(cx, frame_w):
    """Calculates relative direction based on center x-coordinate."""
    ratio = cx / frame_w
    if ratio < 0.35: return "to your left"
    if ratio > 0.65: return "to your right"
    return "ahead"

def get_proximity(bbox_area, frame_area):
    """Calculates proximity based on bounding box size relative to frame."""
    ratio = bbox_area / frame_area
    if ratio > 0.12: return "very close"
    if ratio > 0.04: return "close"
    return ""

def build_alert_phrase(class_name, proximity, direction):
    """Constructs a natural language alert."""
    raw = f"{class_name.capitalize()} {proximity} {direction}"
    return " ".join(raw.split())

# ─────────────────────────────────────────────────────────────────────────────
#  API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"status": "online", "message": "SafeStride AI Backend is running"}

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """Receives an image, runs YOLO inference, and returns formatted detections."""
    try:
        # Read image
        contents = await file.read()
        file_size = len(contents)
        print(f"Received frame: {file.filename}, Size: {file_size} bytes")

        if file_size == 0:
            return {"results": [], "warning": "Received empty file"}

        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as img_err:
            print(f"Image decode error: {img_err}")
            # If standard decoding fails, it might be raw YUV/Grayscale bytes.
            # We return an error so the user can see it in logs/UI.
            return {
                "results": [], 
                "error": "Invalid image format. Ensure the mobile app is sending a valid JPEG/PNG.",
                "details": str(img_err)
            }

        frame = np.array(image)
        frame_h, frame_w, _ = frame.shape
        frame_area = frame_w * frame_h
        
        # Run inference
        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
        
        detections = []
        for box in results.boxes:
            # Box coordinates
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            # Metadata
            cls_id = int(box.cls[0])
            label = results.names[cls_id]
            conf = float(box.conf[0])
            
            # Logic calculations
            cx = (x1 + x2) / 2
            bbox_area = (x2 - x1) * (y2 - y1)
            
            direction = get_direction(cx, frame_w)
            proximity = get_proximity(bbox_area, frame_area)
            alert_text = build_alert_phrase(label, proximity, direction)
            
            detections.append({
                "label": label,
                "confidence": conf,
                "direction": direction,
                "proximity": proximity,
                "alert_text": alert_text,
                "bbox": {
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2)
                }
            })
            
        return {
            "results": detections,
            "width": int(frame_w),
            "height": int(frame_h)
        }
    
    except Exception as e:
        print(f"Server error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

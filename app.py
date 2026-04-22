import io
import os
import cv2
import numpy as np
import time
from PIL import Image, ImageOps
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
import torch

# Import services
from main import DetectionService
from ocr_engine import OCRService

app = FastAPI(title="SafeStride AI Backend")

# Initialize Services
detection_service = DetectionService()
ocr_service = OCRService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "SafeStride AI Backend v3.0 (Orchestrator)"}

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Detection Endpoint using DetectionService from main.py
    """
    try:
        contents = await file.read()
        if len(contents) == 0:
            return {"results": [], "warning": "Empty frame"}

        # Decode image
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = ImageOps.exif_transpose(image)
        frame = np.array(image)
        
        # Process via Detection Service
        result = detection_service.process_frame(frame)
        
        return result
    
    except Exception as e:
        print(f"Detection error: {e}")
        return {"error": str(e)}

@app.post("/ocr")
async def perform_ocr(
    file: UploadFile = File(...),
    flip: bool = Query(False)
):
    """
    OCR Endpoint using OCRService from ocr_engine.py
    """
    try:
        contents = await file.read()
        if len(contents) == 0:
            return {"error": "Empty file", "text": ""}
            
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Fix Orientation and Mirroring
        image = ImageOps.exif_transpose(image)
        if flip:
            image = ImageOps.mirror(image)
            
        img_np = np.array(image)
        
        # Process via OCR Service
        text = ocr_service.extract_text(img_np)
        
        return {
            "text": text,
            "char_count": len(text)
        }
    except Exception as e:
        print(f"OCR error: {e}")
        return {"error": str(e), "text": ""}

if __name__ == "__main__":
    import uvicorn
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)

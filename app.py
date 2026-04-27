import io
import os
import cv2
import numpy as np
import time
from PIL import Image, ImageOps
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch

# Import services
from main import DetectionService
from ocr_engine import OCRService
from database import connect_db, disconnect_db
from sos_service import (
    trigger_sos, 
    send_location_update, 
    get_sos_history, 
    add_contact, 
    remove_contact, 
    get_contacts
)

# Pydantic models for SOS endpoints
class SOSTriggerPayload(BaseModel):
    user_id: str
    lat: float
    lng: float
    message: str = "I need immediate help!"
    call_first: str = None

class LocationUpdatePayload(BaseModel):
    user_id: str
    lat: float
    lng: float

class ContactPayload(BaseModel):
    user_id: str
    name: str
    phone: str

class ContactRemovePayload(BaseModel):
    user_id: str
    phone: str

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

@app.on_event("startup")
async def startup_event():
    await connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await disconnect_db()

@app.get("/")
def read_root():
    return {"status": "online", "message": "SafeStride AI Backend v4.0 (Cloud Ready)"}

@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    heatmap: bool = Query(False)
):
    """
    Detection Endpoint with optional XAI Heatmap.
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
        result = detection_service.process_frame(frame, include_heatmap=heatmap)
        
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

# --- SOS & CONTACT MANAGEMENT ---

@app.post("/sos/trigger")
async def sos_trigger(payload: SOSTriggerPayload):
    """🚨 Fire SOS — SMS all contacts + voice call primary contact."""
    return await trigger_sos(
        user_id=payload.user_id,
        lat=payload.lat,
        lng=payload.lng,
        message=payload.message,
        call_first=payload.call_first,
    )

@app.post("/sos/location")
async def sos_location_update(payload: LocationUpdatePayload):
    """Send a follow-up live location SMS."""
    return await send_location_update(payload.user_id, payload.lat, payload.lng)

@app.get("/sos/history/{user_id}")
async def sos_history(user_id: str, limit: int = Query(10, le=50)):
    """Fetch recent SOS events for a user."""
    logs = await get_sos_history(user_id, limit)
    return {"user_id": user_id, "logs": logs}

@app.post("/sos/contacts/add")
async def add_emergency_contact(payload: ContactPayload):
    """Register a new emergency contact."""
    return await add_contact(payload.user_id, payload.name, payload.phone)

@app.post("/sos/contacts/remove")
async def remove_emergency_contact(payload: ContactRemovePayload):
    """Remove an emergency contact."""
    return await remove_contact(payload.user_id, payload.phone)

@app.get("/sos/contacts/{user_id}")
async def list_emergency_contacts(user_id: str):
    """List all emergency contacts for a user."""
    contacts = await get_contacts(user_id)
    return {"user_id": user_id, "contacts": contacts}

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)



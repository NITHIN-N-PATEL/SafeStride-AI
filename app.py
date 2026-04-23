"""
app.py — SafeStride AI Backend v4.0
All routes are async. MongoDB connected via lifespan.
"""

import io
import numpy as np
from contextlib import asynccontextmanager
from PIL import Image, ImageOps
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import DetectionService
from ocr_engine import OCRService
from database import connect_db, disconnect_db
from sos_service import (
    add_contact, remove_contact, get_contacts,
    trigger_sos, send_location_update, get_sos_history,
)


# ── App lifespan (replaces deprecated on_event) ──────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()          # startup
    yield
    await disconnect_db()       # shutdown


app = FastAPI(title="SafeStride AI Backend", version="4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detection_service = DetectionService()
ocr_service       = OCRService()


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ContactPayload(BaseModel):
    user_id: str
    name: str
    phone: str              # E.164 format: "+919876543210"

class RemoveContactPayload(BaseModel):
    user_id: str
    phone: str

class SOSTriggerPayload(BaseModel):
    user_id: str
    lat: float
    lng: float
    message: str = "I need immediate help!"
    call_first: str | None = None

class LocationUpdatePayload(BaseModel):
    user_id: str
    lat: float
    lng: float


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return {"status": "online", "message": "SafeStride AI Backend v4.0"}


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    heatmap: bool = Query(False)
):
    """
    Detect hazards in a frame.
    ?heatmap=true -> returns a base64 Grad-CAM heatmap overlay
    """
    try:
        contents = await file.read()
        if not contents:
            return {"results": [], "warning": "Empty frame"}
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = ImageOps.exif_transpose(image)
        return detection_service.process_frame(np.array(image), include_heatmap=heatmap)
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# OCR
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/ocr")
async def perform_ocr(
    file: UploadFile = File(...),
    flip: bool = Query(False),
):
    """
    Extract text from an image.
    ?flip=true  -> mirror image before OCR (front cameras)
    """
    try:
        contents = await file.read()
        if not contents:
            return {"error": "Empty file", "text": ""}

        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = ImageOps.exif_transpose(image)
        if flip:
            image = ImageOps.mirror(image)

        text = ocr_service.extract_text(np.array(image))

        if not text:
            return {"text": "", "char_count": 0, "message": "No text detected."}

        return {"text": text, "char_count": len(text)}

    except Exception as e:
        return {"error": str(e), "text": ""}


# ═══════════════════════════════════════════════════════════════════════════════
# SOS — CONTACTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/sos/contacts/add")
async def sos_add_contact(payload: ContactPayload):
    return await add_contact(payload.user_id, payload.name, payload.phone)

@app.post("/sos/contacts/remove")
async def sos_remove_contact(payload: RemoveContactPayload):
    return await remove_contact(payload.user_id, payload.phone)

@app.get("/sos/contacts/{user_id}")
async def sos_get_contacts(user_id: str):
    contacts = await get_contacts(user_id)
    return {"user_id": user_id, "contacts": contacts, "count": len(contacts)}


# ═══════════════════════════════════════════════════════════════════════════════
# SOS — TRIGGER & LOCATION
# ═══════════════════════════════════════════════════════════════════════════════

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
    """Send a follow-up live location SMS. Call every ~2 min after SOS trigger."""
    return await send_location_update(payload.user_id, payload.lat, payload.lng)

@app.get("/sos/history/{user_id}")
async def sos_history(user_id: str, limit: int = Query(10, le=50)):
    """Fetch recent SOS events for a user (for app history screen)."""
    logs = await get_sos_history(user_id, limit)
    return {"user_id": user_id, "logs": logs}


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
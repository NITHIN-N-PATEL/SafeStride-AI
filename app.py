import io
import os
import cv2
import numpy as np
import time
from contextlib import asynccontextmanager
from PIL import Image, ImageOps
from fastapi import FastAPI, File, UploadFile, Query, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from main import DetectionService
from ocr_engine import OCRService
from navigation import router as navigation_router
from database import connect_db, disconnect_db
from sos_service import (
    trigger_sos, send_location_update, get_sos_history,
    add_contact, remove_contact, get_contacts, resolve_sos,
)


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SAFESTRIDE_API_KEY = os.getenv("SAFESTRIDE_API_KEY")


async def verify_api_key(x_api_key: str = Header(None)):
    """Validates X-API-Key header. Skipped if SAFESTRIDE_API_KEY is not set."""
    if not SAFESTRIDE_API_KEY:
        return
    if x_api_key != SAFESTRIDE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")



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

class SOSResolvePayload(BaseModel):
    user_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(title="SafeStride AI", version="5.0", lifespan=lifespan)

detection_service = DetectionService()
ocr_service = OCRService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register navigation router
app.include_router(navigation_router, prefix="/navigation", tags=["Navigation"])


@app.get("/")
def health():
    return {"status": "online", "version": "5.0"}


@app.post("/detect", dependencies=[Depends(verify_api_key)])
async def detect(file: UploadFile = File(...), heatmap: bool = Query(False), language: str = Query("en")):
    """Run hazard detection on an uploaded image."""
    try:
        contents = await file.read()
        if len(contents) == 0:
            return {"results": [], "warning": "Empty frame"}

        if len(contents) > MAX_UPLOAD_BYTES:
            return {"error": "File too large"}

        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = ImageOps.exif_transpose(image)
        frame = np.array(image)
        return detection_service.process_frame(frame, include_heatmap=heatmap, language=language)
    
    except Exception as e:
        print(f"[Detection] Error: {e}")
        return {"error": str(e)}


@app.post("/ocr", dependencies=[Depends(verify_api_key)])
async def perform_ocr(
    file: UploadFile = File(...),
    flip: bool = Query(False),
    language: str = Query("en", description="Language code: en, hi, ta, te, kn, bn, mr, ne")
):
    """Extract text from an uploaded image."""
    try:
        contents = await file.read()
        if len(contents) == 0:
            return {"error": "Empty file", "text": ""}

        if len(contents) > MAX_UPLOAD_BYTES:
            return {"error": "File too large", "text": ""}
            
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        image = ImageOps.exif_transpose(image)
        if flip:
            image = ImageOps.mirror(image)

        img_np = np.array(image)
        text = ocr_service.extract_text(img_np, language=language)
        
        return {
            "text": text,
            "char_count": len(text),
            "language": language
        }
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return {"error": str(e), "text": ""}

# SOS & Contact Management

@app.post("/sos/trigger", dependencies=[Depends(verify_api_key)])
async def sos_trigger(payload: SOSTriggerPayload):
    """Trigger SOS — SMS all contacts + voice call primary contact."""
    return await trigger_sos(
        user_id=payload.user_id,
        lat=payload.lat,
        lng=payload.lng,
        message=payload.message,
        call_first=payload.call_first,
    )

@app.post("/sos/resolve", dependencies=[Depends(verify_api_key)])
async def sos_resolve(payload: SOSResolvePayload):
    """Resolve an active SOS session."""
    return await resolve_sos(payload.user_id)

@app.post("/sos/location", dependencies=[Depends(verify_api_key)])
async def sos_location_update(payload: LocationUpdatePayload):
    """Send a follow-up live location SMS to all contacts."""
    return await send_location_update(payload.user_id, payload.lat, payload.lng)

@app.get("/sos/history/{user_id}", dependencies=[Depends(verify_api_key)])
async def sos_history(user_id: str, limit: int = Query(10, le=50)):
    """Fetch recent SOS events for a user."""
    logs = await get_sos_history(user_id, limit)
    return {"user_id": user_id, "logs": logs}

@app.post("/sos/contacts/add", dependencies=[Depends(verify_api_key)])
async def add_emergency_contact(payload: ContactPayload):
    """Register a new emergency contact."""
    return await add_contact(payload.user_id, payload.name, payload.phone)

@app.post("/sos/contacts/remove", dependencies=[Depends(verify_api_key)])
async def remove_emergency_contact(payload: ContactRemovePayload):
    """Remove an emergency contact."""
    return await remove_contact(payload.user_id, payload.phone)

@app.get("/sos/contacts/{user_id}", dependencies=[Depends(verify_api_key)])
async def list_emergency_contacts(user_id: str):
    """List all emergency contacts for a user."""
    contacts = await get_contacts(user_id)
    return {"user_id": user_id, "contacts": contacts}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

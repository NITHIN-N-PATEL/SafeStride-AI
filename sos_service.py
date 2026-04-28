"""
sos_service.py — SOS emergency contact management and alert service.
"""

from datetime import datetime, timezone, timedelta
import os
from twilio.rest import Client
from database import get_db

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

SOS_DEDUP_WINDOW = 30  # seconds


# Contact Management

async def add_contact(user_id: str, name: str, phone: str) -> dict:
    """Add or update an emergency contact for a user."""
    db = get_db()
    contact = {
        "user_id": user_id,
        "name": name,
        "phone": phone,
        "added_at": datetime.now(timezone.utc),
    }
    result = await db.contacts.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": contact},
        upsert=True,
    )
    status = "updated" if result.matched_count else "created"
    print(f"[SOS] Contact {status}: {name} ({phone}) for user '{user_id}'")
    return {"status": status, "contact": {**contact, "phone": phone}}


async def get_contacts(user_id: str) -> list:
    """Retrieve all emergency contacts for a user."""
    db = get_db()
    cursor = db.contacts.find({"user_id": user_id}, {"_id": 0})
    return await cursor.to_list(length=100)


async def remove_contact(user_id: str, phone: str) -> dict:
    """Remove an emergency contact by phone number."""
    db = get_db()
    result = await db.contacts.delete_one({"user_id": user_id, "phone": phone})
    removed = result.deleted_count > 0
    print(f"[SOS] Contact removal ({'success' if removed else 'not found'}): {phone} for user '{user_id}'")
    return {"status": "removed" if removed else "not_found", "phone": phone}


# Twilio SMS & Voice

def _get_twilio_client():
    """Returns a Twilio client if credentials are configured."""
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_NUMBER]):
        return None
    return Client(TWILIO_SID, TWILIO_AUTH)


async def send_sms(contacts: list, message: str, lat: float, lng: float):
    """Send SMS with location link to all contacts."""
    client = _get_twilio_client()
    if not client:
        print("[SOS] Twilio not configured, skipping SMS.")
        return

    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    body = f"{message}\n\nLive Location: {maps_link}"

    for contact in contacts:
        try:
            client.messages.create(
                body=body,
                from_=TWILIO_NUMBER,
                to=contact["phone"]
            )
            print(f"[SOS] SMS sent to {contact['phone']}")
        except Exception as e:
            print(f"[SOS] Error sending SMS to {contact['phone']}: {e}")


async def make_voice_call(phone: str, user_id: str):
    """Initiate an automated voice call to a contact."""
    client = _get_twilio_client()
    if not client:
        print("[SOS] Twilio not configured, skipping voice call.")
        return

    twiml = f'<Response><Say voice="alice">Emergency alert from SafeStride AI. User {user_id} needs help. Please check your messages for their location.</Say></Response>'

    try:
        client.calls.create(
            twiml=twiml,
            from_=TWILIO_NUMBER,
            to=phone
        )
        print(f"[SOS] Voice call initiated to {phone}")
    except Exception as e:
        print(f"[SOS] Error initiating voice call: {e}")


# SOS Trigger

async def trigger_sos(
    user_id: str,
    lat: float,
    lng: float,
    message: str = "SOS triggered via SafeStride AI! I need immediate help.",
    call_first: str = None,
) -> dict:
    """Trigger an SOS alert. Sends SMS to all contacts and calls the primary one."""
    db = get_db()

    # Deduplication: reject rapid double-taps within the window
    dedup_cutoff = datetime.now(timezone.utc) - timedelta(seconds=SOS_DEDUP_WINDOW)
    recent_sos = await db.sos_logs.find_one(
        {"user_id": user_id, "triggered_at": {"$gte": dedup_cutoff}}
    )
    if recent_sos:
        print(f"[SOS] Duplicate trigger blocked for user '{user_id}' (within {SOS_DEDUP_WINDOW}s window)")
        return {
            "status": "duplicate",
            "message": f"SOS already triggered within the last {SOS_DEDUP_WINDOW} seconds.",
            "sos_id": str(recent_sos["_id"]),
        }

    contacts = await get_contacts(user_id)
    if not contacts:
        return {"status": "error", "message": "No emergency contacts found"}

    if call_first:
        contacts = sorted(contacts, key=lambda c: (c["phone"] != call_first))

    sos_log = {
        "user_id": user_id,
        "location": {"lat": lat, "lng": lng},
        "message": message,
        "call_first": call_first,
        "contacts_notified": [c["phone"] for c in contacts],
        "triggered_at": datetime.now(timezone.utc),
        "status": "triggered",
    }

    result = await db.sos_logs.insert_one(sos_log)
    sos_log["_id"] = str(result.inserted_id)

    print(f"[SOS] ALERT triggered for user '{user_id}' at ({lat}, {lng}).")

    await send_sms(contacts, message, lat, lng)
    await make_voice_call(contacts[0]["phone"], user_id)

    return {
        "status": "triggered",
        "sos_id": sos_log["_id"],
        "location": sos_log["location"],
        "contacts_notified": contacts,
        "triggered_at": sos_log["triggered_at"].isoformat(),
    }


# SOS History & Location Updates

async def get_sos_history(user_id: str, limit: int = 10) -> list:
    """Retrieve SOS event history for a user, newest first."""
    db = get_db()
    cursor = (
        db.sos_logs
        .find({"user_id": user_id}, {"_id": 0})
        .sort("triggered_at", -1)
        .limit(limit)
    )
    logs = await cursor.to_list(length=limit)

    for log in logs:
        if isinstance(log.get("triggered_at"), datetime):
            log["triggered_at"] = log["triggered_at"].isoformat()
    return logs


async def send_location_update(user_id: str, lat: float, lng: float) -> dict:
    """Log a live location update and re-notify contacts via SMS."""
    db = get_db()

    latest_sos = await db.sos_logs.find_one(
        {"user_id": user_id},
        sort=[("triggered_at", -1)]
    )
    if not latest_sos:
        return {"status": "error", "message": "No active SOS found for user"}

    update_entry = {
        "location": {"lat": lat, "lng": lng},
        "updated_at": datetime.now(timezone.utc),
    }

    await db.sos_logs.update_one(
        {"_id": latest_sos["_id"]},
        {"$push": {"location_updates": update_entry}}
    )

    print(f"[SOS] Location update for user '{user_id}': ({lat}, {lng})")

    # Re-notify contacts with updated location
    contacts_phones = latest_sos.get("contacts_notified", [])
    if contacts_phones:
        contacts = [{"phone": p, "name": "Contact"} for p in contacts_phones]
        await send_sms(contacts, f"Live location update from SafeStride AI user {user_id}", lat, lng)

    return {
        "status": "location_updated",
        "user_id": user_id,
        "lat": lat,
        "lng": lng,
        "timestamp": update_entry["updated_at"].isoformat()
    }


async def resolve_sos(user_id: str) -> dict:
    """Mark the most recent active SOS for a user as resolved."""
    db = get_db()

    latest_sos = await db.sos_logs.find_one(
        {"user_id": user_id, "status": "triggered"},
        sort=[("triggered_at", -1)]
    )
    if not latest_sos:
        return {"status": "error", "message": "No active SOS found for user"}

    await db.sos_logs.update_one(
        {"_id": latest_sos["_id"]},
        {"$set": {
            "status": "resolved",
            "resolved_at": datetime.now(timezone.utc)
        }}
    )

    print(f"[SOS] SOS resolved for user '{user_id}'")
    return {
        "status": "resolved",
        "sos_id": str(latest_sos["_id"]),
        "resolved_at": datetime.now(timezone.utc).isoformat()
    }

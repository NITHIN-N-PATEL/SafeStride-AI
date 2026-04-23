"""
sos.py — SOS emergency contact management and alert logging for SafeStride AI

Collections used (defined in database.py):
  - db.contacts  : stores emergency contacts per user
  - db.sos_logs  : stores SOS trigger history per user
"""

from datetime import datetime, timezone
import os
from twilio.rest import Client
from database import get_db

# Twilio Configuration (Set these in your .env)
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")



async def add_contact(user_id: str, name: str, phone: str) -> dict:
    """
    Add (or update) an emergency contact for a user.

    Args:
        user_id: Unique identifier for the user.
        name:    Display name of the emergency contact.
        phone:   Phone number of the emergency contact.

    Returns:
        A dict with the result status and the contact document.
    """
    db = get_db()
    contact = {
        "user_id": user_id,
        "name": name,
        "phone": phone,
        "added_at": datetime.now(timezone.utc),
    }

    # Upsert: update if (user_id, phone) pair already exists, else insert.
    result = await db.contacts.update_one(
        {"user_id": user_id, "phone": phone},
        {"$set": contact},
        upsert=True,
    )

    status = "updated" if result.matched_count else "created"
    print(f"[SOS] Contact {status}: {name} ({phone}) for user '{user_id}'")
    return {"status": status, "contact": {**contact, "phone": phone}}


async def get_contacts(user_id: str) -> list:
    """
    Retrieve all emergency contacts for a user.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        List of contact documents (dicts).
    """
    db = get_db()
    cursor = db.contacts.find({"user_id": user_id}, {"_id": 0})
    return await cursor.to_list(length=100)


async def remove_contact(user_id: str, phone: str) -> dict:
    """
    Remove an emergency contact for a user by phone number.

    Args:
        user_id: Unique identifier for the user.
        phone:   Phone number of the contact to remove.

    Returns:
        A dict with the deletion status.
    """
    db = get_db()
    result = await db.contacts.delete_one({"user_id": user_id, "phone": phone})
    removed = result.deleted_count > 0
    print(f"[SOS] Contact removal ({'success' if removed else 'not found'}): {phone} for user '{user_id}'")
    return {"status": "removed" if removed else "not_found", "phone": phone}


# ---------------------------------------------------------------------------
# SOS Trigger
# ---------------------------------------------------------------------------

async def send_sms(contacts: list, message: str, lat: float, lng: float):
    """Sends real SMS alerts to all contacts with a live map link."""
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_NUMBER]):
        print("[SOS] Warning: Twilio credentials missing in .env. Skipping SMS.")
        return

    client = Client(TWILIO_SID, TWILIO_AUTH)
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    full_message = f"🚨 {message}\n\nLive Location: {maps_link}"

    for contact in contacts:
        try:
            client.messages.create(
                body=full_message,
                from_=TWILIO_NUMBER,
                to=contact["phone"]
            )
            print(f"[SOS] SMS sent to {contact['name']} ({contact['phone']})")
        except Exception as e:
            print(f"[SOS] Error sending SMS to {contact['phone']}: {str(e)}")


async def make_voice_call(to_phone: str, user_name: str):
    """Initiates a real voice call via Twilio and speaks an alert message."""
    if not all([TWILIO_SID, TWILIO_AUTH, TWILIO_NUMBER]):
        print("[SOS] Warning: Twilio credentials missing. Skipping Voice Call.")
        return

    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        # TwiML instructions for what the call should "say"
        twiml_msg = f"<Response><Say voice='alice'>Emergency Alert from SafeStride AI. User {user_name} has triggered an SOS. Please check your messages for their live location link.</Say></Response>"
        
        client.calls.create(
            twiml=twiml_msg,
            to=to_phone,
            from_=TWILIO_NUMBER
        )
        print(f"[SOS] Voice call initiated to {to_phone}")
    except Exception as e:
        print(f"[SOS] Error initiating voice call: {str(e)}")


async def trigger_sos(
    user_id: str,
    lat: float,
    lng: float,
    message: str = "SOS triggered via SafeStride AI! I need immediate help.",
    call_first: str = None,
) -> dict:
    db = get_db()
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

    # 🔥 1. SEND REAL SMS to everyone
    await send_sms(contacts, message, lat, lng)

    # 🔥 2. MAKE VOICE CALL to the primary contact
    primary_contact = contacts[0]
    await make_voice_call(primary_contact["phone"], user_id)

    return {
        "status": "triggered",
        "sos_id": sos_log["_id"],
        "location": sos_log["location"],
        "contacts_notified": contacts,
        "triggered_at": sos_log["triggered_at"].isoformat(),
    }


# ---------------------------------------------------------------------------
# SOS History
# ---------------------------------------------------------------------------

async def get_sos_history(user_id: str, limit: int = 10) -> list:
    """
    Retrieve the SOS trigger history for a user, newest first.

    Args:
        user_id: Unique identifier for the user.
        limit:   Maximum number of records to return (default 10).

    Returns:
        List of SOS log documents.
    """
    db = get_db()
    cursor = (
        db.sos_logs
        .find({"user_id": user_id}, {"_id": 0})
        .sort("triggered_at", -1)
        .limit(limit)
    )
    logs = await cursor.to_list(length=limit)

    # Serialise datetime objects to ISO strings for JSON friendliness.
    for log in logs:
        if isinstance(log.get("triggered_at"), datetime):
            log["triggered_at"] = log["triggered_at"].isoformat()

    return logs


async def send_location_update(user_id: str, lat: float, lng: float) -> dict:
    """
    Send a follow-up live location update for an active SOS.
    Logs the update to the latest SOS session.

    Args:
        user_id: Unique identifier for the user.
        lat:     Updated latitude.
        lng:     Updated longitude.

    Returns:
        A dict with the status and location.
    """
    db = get_db()
    
    # Find the most recent SOS trigger for this user
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

    # Push the update to the sos_logs entry
    await db.sos_logs.update_one(
        {"_id": latest_sos["_id"]},
        {"$push": {"location_updates": update_entry}}
    )

    print(f"[SOS] Location update for user '{user_id}': ({lat}, {lng})")
    
    # In a real app, you'd send an SMS here:
    # await send_location_sms(latest_sos['contacts_notified'], lat, lng)

    return {
        "status": "location_updated",
        "user_id": user_id,
        "lat": lat,
        "lng": lng,
        "timestamp": update_entry["updated_at"].isoformat()
    }

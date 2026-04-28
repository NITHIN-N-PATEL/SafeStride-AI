import asyncio
import os
from database import connect_db, disconnect_db, get_db
from sos_service import add_contact, trigger_sos, get_sos_history

async def main():
    await connect_db()

    # 1. Clear history for a clean test
    db = get_db()
    await db.sos_logs.drop()
    await db.contacts.drop()
    print("[TEST] Database cleared for fresh run.")

    MY_REAL_PHONE = "+919964446467" 
    
    print(f"[TEST] Adding contact: {MY_REAL_PHONE}")
    await add_contact("user1", "My Phone", MY_REAL_PHONE)

    # 3. Trigger the SOS
    print("[TEST] Triggering SOS...")
    result = await trigger_sos(
        user_id="user1",
        lat=12.9716,
        lng=77.5946,
        message="SafeStride LIVE TEST: I need help!",
        call_first=MY_REAL_PHONE
    )
    
    print("\n--- TRIGGER RESULT ---")
    print(result)
    print("----------------------\n")

    # 4. Check History
    history = await get_sos_history("user1", limit=1)
    print(f"[TEST] History check (latest): {history}")

    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(main())

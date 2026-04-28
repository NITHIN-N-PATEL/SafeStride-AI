"""
database.py — MongoDB connection and collection indexing.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/safestride")
MAX_RETRIES = 3
RETRY_DELAY = 2

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Connect to MongoDB with retry logic. Called on app startup."""
    global client, db

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            await client.admin.command("ping")
            db = client.get_default_database()
            print(f"[Database] MongoDB connected → {db.name}")

            await db.contacts.create_index(
                [("user_id", 1), ("phone", 1)], unique=True
            )
            await db.sos_logs.create_index(
                [("user_id", 1), ("triggered_at", -1)]
            )
            return

        except Exception as e:
            print(f"[Database] Connection attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
            else:
                print("[Database] WARNING: Could not connect to MongoDB.")


async def disconnect_db():
    """Close the MongoDB connection. Called on app shutdown."""
    if client:
        client.close()
        print("[Database] MongoDB disconnected.")


def get_db():
    """Returns the database handle. Raises if not connected."""
    if db is None:
        raise RuntimeError("Database not initialized.")
    return db
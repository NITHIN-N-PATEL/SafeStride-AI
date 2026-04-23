"""
database.py — MongoDB connection + collections
Uses Motor (async MongoDB driver, built for FastAPI)
Install: pip install motor pymongo python-dotenv

.env file:
  MONGO_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/safestride
"""

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/safestride")

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    """Call on FastAPI startup."""
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db     = client.get_default_database()
    print(f"MongoDB connected -> {db.name}")

    
    await db.contacts.create_index(
        [("user_id", 1), ("phone", 1)], unique=True  # no duplicate contacts
    )
    await db.sos_logs.create_index(
        [("user_id", 1), ("triggered_at", -1)]        # fast log queries per user
    )


async def disconnect_db():
    """Call on FastAPI shutdown."""
    if client:
        client.close()
        print("MongoDB disconnected.")


def get_db():
    return db
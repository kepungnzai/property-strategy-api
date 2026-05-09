import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "property_analysis")

_client = None
_db = None

async def get_database():
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[MONGO_DB]
    return _db


async def close_database():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None

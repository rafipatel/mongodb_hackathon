from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from config import MONGODB_URI, MONGODB_DB

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[MONGODB_DB]


def get_collection(name: str) -> AsyncIOMotorCollection:
    return get_db()[name]


async def ping() -> bool:
    """Verify Atlas connectivity."""
    try:
        await get_client().admin.command("ping")
        return True
    except Exception:
        return False

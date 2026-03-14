from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import config


class Database:
    client: AsyncIOMotorClient = None
    db = None


db_instance = Database()


async def connect_to_db():
    db_instance.client = AsyncIOMotorClient(config.MONGO_URI)
    db_instance.db = db_instance.client[config.DB_NAME]
    print("Connected to MongoDB")

    from app.services.jaw_service import JAWService
    await JAWService.setup_jaw_indexes()


async def close_db_connection():
    if db_instance.client:
        db_instance.client.close()
        print("MongoDB connection closed")

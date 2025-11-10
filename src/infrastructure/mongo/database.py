# src/infrastructure/mongo/database.py

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from ...config.settings import settings

class MongoDatabase:
    """MongoDB connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_to_mongo(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.db = cls.client[settings.MONGODB_DB_NAME]
        # Create indexes
        await cls._create_indexes()
    
    @classmethod
    async def close_mongo_connection(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
    
    @classmethod
    async def _create_indexes(cls):
        """Create database indexes"""
        posts_collection = cls.db["posts"]
        
        # Create indexes
        await posts_collection.create_index("slug", unique=True)
        await posts_collection.create_index("status")
        await posts_collection.create_index("published_at")
        await posts_collection.create_index("tags")
        # await posts_collection.create_index("author_id")
        
        # Other collections
        await cls.db["categories"].create_index("slug", unique=True)
        # await cls.db["authors"].create_index("email", unique=True)
        # await cls.db["authors"].create_index("username", unique=True)

def get_database() -> AsyncIOMotorDatabase:
    """Dependency: Get MongoDB database"""
    return MongoDatabase.db
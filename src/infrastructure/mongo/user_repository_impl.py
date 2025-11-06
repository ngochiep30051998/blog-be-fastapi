from datetime import datetime, timezone
from src.domain.users.entity import UserEntity
from src.domain.users.repository import UserRepository

from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoUserRepository(UserRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["users"]

    async def get_by_email(self, email: str) -> UserEntity:
        result = await self.collection.find_one({"email": email})
        return result
    
    async def create_user(self, user: UserEntity)-> UserEntity:
        data = {
            "_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role,
            "date_of_birth": user.date_of_birth,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        await self.collection.update_one(
            {"_id": data["_id"]},
            {"$set": data},
            upsert=True
        )
        data.pop("password_hash", None) # Do not return password hash
        return data
    
    async def delete(self, user_id):
        result = await self.collection.update_one({"_id": user_id}, {"$set": {"deleted_at": datetime.now(timezone.utc)}})
        return result.modified_count > 0
    
    async def update_user(self, user_id, user_data):
        await self.collection.update_one({"_id": user_id}, {"$set": user_data})
        return user_data
    
    async def list_users(self, skip: int = 0, limit: int = 10):
        cursor = self.collection.find({"deleted_at": None}).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        return users

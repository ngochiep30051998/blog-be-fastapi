from src.domain.files.repository import FileRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoFileRepository(FileRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["files"]

    async def create_file(self, file_data):
        result = await self.collection.insert_one(file_data)
        return str(result.inserted_id)

    async def get_by_id(self, file_id):
        file_data = await self.collection.find_one({"_id": file_id})
        return file_data

    async def update_file(self, file_id, file_data):
        await self.collection.update_one({"_id": file_id}, {"$set": file_data})

    async def delete(self, file_id):
        await self.collection.delete_one({"_id": file_id})

    async def list_files(self, skip: int = 0, limit: int = 10):
        cursor = self.collection.find().skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def count_files(self) -> int:
        """Count all non-deleted files"""
        return await self.collection.count_documents({"deleted_at": None})
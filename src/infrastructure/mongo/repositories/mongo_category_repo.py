from src.domain.blog.entities.catetory_entity import CategoryEntity
from src.domain.blog.repositories.category_repo import CategoryRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

class MongoCategoryRepository(CategoryRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["categories"]
    async def create_category(self, category: CategoryEntity)-> CategoryEntity:
        category_data = {
            "_id": category.id,
            "name": category.name,
            "description": category.description,
            "slug": str(category.slug),
            "path": category.path,
            "parent_id": category.parent_id,
            "created_at": category.created_at,
            "updated_at": category.updated_at
        }
        await self.collection.update_one(
            {"_id": category.id},
            {"$set": category_data},
            upsert=True
        )
        return category

    async def get_by_id(self, category_id):
        result = await self.collection.find_one({"_id": category_id})
        return result

    async def update_category(self, category_id, category_data):
        await self.collection.update_one({"_id": category_id}, {"$set": category_data})
        return category_data

    async def delete(self, id):
        result = await self.collection.delete_one({"_id": id})
        return result.deleted_count > 0

    async def list_categories(self, skip: int = 0, limit: int = 10):
        cursor = self.db["categories"].find({"deleted_at": None }).skip(skip).limit(limit)
        categories = await cursor.to_list(length=limit)
        return categories
    async def count_categories(self) -> int:
        """Count all non-deleted count_categories"""
        return await self.collection.count_documents({"deleted_at": None})
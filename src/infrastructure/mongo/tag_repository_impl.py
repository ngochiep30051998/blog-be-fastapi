from typing import List, Optional
from bson import ObjectId
from src.core.value_objects.slug import Slug
from src.domain.tags.entity import TagEntity
from src.domain.tags.repository import TagRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone


class MongoTagRepository(TagRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["tags"]

    async def create_tag(self, tag: TagEntity) -> TagEntity:
        """Save tag to MongoDB"""
        tag_data = {
            "_id": tag.id,
            "name": tag.name,
            "slug": str(tag.slug),
            "description": tag.description,
            "usage_count": tag.usage_count,
            "created_at": tag.created_at,
            "updated_at": tag.updated_at
        }
        await self.collection.update_one(
            {"_id": tag.id},
            {"$set": tag_data},
            upsert=True
        )
        return tag_data

    async def get_by_id(self, tag_id) -> Optional[dict]:
        result = await self.collection.find_one({"_id": ObjectId(tag_id), "deleted_at": None})
        return result

    async def get_by_slug(self, slug: str) -> Optional[dict]:
        """Get tag by slug"""
        result = await self.collection.find_one({"slug": slug, "deleted_at": None})
        return result

    async def get_by_name(self, name: str) -> Optional[dict]:
        """Get tag by name (case-insensitive)"""
        result = await self.collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}, "deleted_at": None})
        return result

    async def get_by_ids(self, tag_ids: list) -> List[dict]:
        """Get multiple tags by their IDs"""
        if not tag_ids:
            return []
        object_ids = [ObjectId(tid) for tid in tag_ids]
        cursor = self.collection.find({"_id": {"$in": object_ids}, "deleted_at": None})
        results = await cursor.to_list(length=None)
        return results

    async def update_tag(self, tag_id, tag_data) -> Optional[dict]:
        """Update tag by ID"""
        await self.collection.update_one({"_id": ObjectId(tag_id)}, {"$set": tag_data})
        return await self.get_by_id(tag_id)

    async def delete(self, id) -> bool:
        """Soft delete tag"""
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"deleted_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0

    async def list_tags(self, skip: int = 0, limit: int = 10) -> List[dict]:
        """List all non-deleted tags"""
        cursor = self.collection.find({"deleted_at": None}).sort("usage_count", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return results

    async def increment_usage_count(self, tag_id) -> None:
        """Increment usage count for a tag"""
        await self.collection.update_one(
            {"_id": ObjectId(tag_id)},
            {"$inc": {"usage_count": 1}}
        )

    async def decrement_usage_count(self, tag_id) -> None:
        """Decrement usage count for a tag"""
        await self.collection.update_one(
            {"_id": ObjectId(tag_id)},
            {"$inc": {"usage_count": -1}}
        )

    async def count_tags(self) -> int:
        """Count all non-deleted tags"""
        return await self.collection.count_documents({"deleted_at": None})


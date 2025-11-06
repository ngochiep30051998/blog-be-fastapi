from typing import List, Optional
from bson import ObjectId
from src.domain.blog.entities.post_entity import PostEntity
from src.domain.blog.repositories.post_repo import PostRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.blog.value_objects.slug import Slug
from src.domain.blog.value_objects.statuses import PostStatus
from datetime import datetime, timezone
class MongoPostRepository(PostRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["posts"]
    async def list_posts(self, skip: int = 0, limit: int = 10):
        pipeline = [
            {"$match": {"deleted_at": None}},
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category"
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        cursor = self.db["posts"].aggregate(pipeline)
        posts = await cursor.to_list(length=limit)
        return posts
    
    async def create_post(self, post: PostEntity) -> PostEntity:
        """Save post to MongoDB"""
        post_data = {
            "_id": post.id,
            "slug": str(post.slug),
            "title": post.title,
            "content": post.content,
            "excerpt": post.excerpt,
            "author_name": post.author_name,
            "author_email": post.author_email,
            "status": post.status.value,
            "tags": post.tags,
            "category_id": post.category_id,
            "views_count": post.views_count,
            "likes_count": post.likes_count,
            # "comments": [
            #     {
            #         "_id": c.id,
            #         "author_name": c.author_name,
            #         "author_email": c.author_email,
            #         "content": c.content,
            #         "status": c.status.value,
            #         "likes": c.likes,
            #         "created_at": c.created_at
            #     }
            #     for c in post.comments
            # ],
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at
        }
        await self.collection.update_one(
            {"_id": post.id},
            {"$set": post_data},
            upsert=True
        )
        return post

    async def get_by_id(self, post_id: ObjectId) -> Optional[dict]:
        pipeline = [
            {"$match": {"_id": ObjectId(post_id),"deleted_at": None}},
            {
                "$lookup": {
                    "from": "categories",            
                    "localField": "category_id",     
                    "foreignField": "_id",           
                    "as": "category"            
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}} 
        ]

        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return None
        return result[0]
    
    async def get_by_slug(self, slug: Slug) -> Optional[PostEntity]:
        """Get post by slug"""
        result = await self.collection.find_one({"slug": str(slug)})
        if not result:
            return None
        return result
    
    async def find_published(self, skip: int = 0, limit: int = 10) -> List[PostEntity]:
        """Find published posts"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return results
    
    async def find_by_tag(self, tag: str, skip: int = 0, limit: int = 10) -> List[PostEntity]:
        """Find posts by tag"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value, "tags": tag}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return results
    
    async def delete(self, post_id: ObjectId) -> bool:
        """Delete post"""
        result = await self.collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"deleted_at": datetime.now(timezone.utc)}})
        return result.modified_count > 0

    async def count_published(self) -> int:
        """Count published posts"""
        return await self.collection.count_documents(
            {"status": PostStatus.PUBLISHED.value}
        )
    
    async def update_post(self, post_id: ObjectId, post_data: dict) -> Optional[PostEntity]:
        """Update post by ID"""
        await self.collection.update_one({"_id": post_id}, {"$set": post_data})
        return await self.get_by_id(post_id)
    async def count_posts(self) -> int:
        """Count all non-deleted posts"""
        return await self.collection.count_documents({"deleted_at": None})
    
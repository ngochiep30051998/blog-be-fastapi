from typing import List, Optional
from bson import ObjectId
from src.core.value_objects.slug import Slug
from src.core.value_objects.statuses import PostStatus
from src.domain.posts.entity import PostEntity
from src.domain.posts.repository import PostRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
class MongoPostRepository(PostRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["posts"]
    async def list_posts(self, skip: int = 0, limit: int = 10):
        # Include $lookup for tags to populate full tag objects in response
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
            {
                "$lookup": {
                    "from": "tags",
                    "localField": "tag_ids",
                    "foreignField": "_id",
                    "as": "tags"
                }
            },
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
            "tag_ids": post.tag_ids,
            "tag_names": post.tag_names,  # Denormalized for faster reads
            "tag_slugs": post.tag_slugs,  # Denormalized tag slugs for faster reads
            "category_id": post.category_id,
            "views_count": post.views_count,
            "likes_count": post.likes_count,
            "thumbnail": post.thumbnail,
            "banner": post.banner,
            # SEO fields
            "meta_title": post.meta_title,
            "meta_description": post.meta_description,
            "meta_keywords": post.meta_keywords,
            "meta_robots": post.meta_robots,
            "og_title": post.og_title,
            "og_description": post.og_description,
            "og_image": post.og_image,
            "og_type": post.og_type,
            "twitter_card": post.twitter_card,
            "twitter_title": post.twitter_title,
            "twitter_description": post.twitter_description,
            "twitter_image": post.twitter_image,
            "canonical_url": post.canonical_url,
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
        # Optimized: No $lookup for tags since tag_names are stored directly
        # Still do $lookup for full tag objects if needed, but tag_names are available immediately
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
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "tags",
                    "localField": "tag_ids",
                    "foreignField": "_id",
                    "as": "tags"
                }
            }
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
    
    async def get_published_by_slug(self, slug: str) -> Optional[dict]:
        """Get published post by slug with lookups for tags and categories"""
        pipeline = [
            {
                "$match": {
                    "slug": slug,
                    "status": PostStatus.PUBLISHED.value,
                    "deleted_at": None
                }
            },
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category"
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "tags",
                    "localField": "tag_ids",
                    "foreignField": "_id",
                    "as": "tags"
                }
            }
        ]
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return None
        return result[0]
    
    async def list_published_posts(self, skip: int = 0, limit: int = 10, category_id: str = None):
        """List published posts with lookups for tags and categories"""
        pipeline = [
            {
                "$match": {
                    "status": PostStatus.PUBLISHED.value,
                    "deleted_at": None
                }
            }
        ]
        
        # Add category filter if provided
        if category_id:
            try:
                category_object_id = ObjectId(category_id)
                pipeline[0]["$match"]["category_id"] = category_object_id
            except:
                pass  # Invalid ObjectId, ignore filter
        
        pipeline.extend([
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category"
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "tags",
                    "localField": "tag_ids",
                    "foreignField": "_id",
                    "as": "tags"
                }
            },
            {"$sort": {"published_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ])
        
        cursor = self.collection.aggregate(pipeline)
        posts = await cursor.to_list(length=limit)
        return posts
    
    async def count_published_posts(self, category_id: str = None) -> int:
        """Count published posts"""
        query = {
            "status": PostStatus.PUBLISHED.value,
            "deleted_at": None
        }
        
        if category_id:
            try:
                query["category_id"] = ObjectId(category_id)
            except:
                pass  # Invalid ObjectId, ignore filter
        
        return await self.collection.count_documents(query)
    
    async def find_published_by_tag_slug(self, tag_slug: str, skip: int = 0, limit: int = 10) -> List[dict]:
        """Find published posts by tag slug with lookups"""
        pipeline = [
            {
                "$match": {
                    "status": PostStatus.PUBLISHED.value,
                    "tag_slugs": tag_slug,
                    "deleted_at": None
                }
            },
            {
                "$lookup": {
                    "from": "categories",
                    "localField": "category_id",
                    "foreignField": "_id",
                    "as": "category"
                }
            },
            {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "tags",
                    "localField": "tag_ids",
                    "foreignField": "_id",
                    "as": "tags"
                }
            },
            {"$sort": {"published_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        return results
    
    async def count_published_by_tag_slug(self, tag_slug: str) -> int:
        """Count published posts by tag slug"""
        return await self.collection.count_documents({
            "status": PostStatus.PUBLISHED.value,
            "tag_slugs": tag_slug,
            "deleted_at": None
        })
    
    async def find_published(self, skip: int = 0, limit: int = 10) -> List[PostEntity]:
        """Find published posts"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return results
    
    async def find_by_tag(self, tag_id: ObjectId, skip: int = 0, limit: int = 10) -> List[PostEntity]:
        """Find posts by tag ID"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value, "tag_ids": tag_id, "deleted_at": None}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return results
    
    async def find_by_tag_name(self, tag_name: str, skip: int = 0, limit: int = 10) -> List[dict]:
        """Find posts by tag name (optimized using denormalized tag_names field)"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value, "tag_names": tag_name, "deleted_at": None}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return results
    
    async def find_by_tag_slug(self, tag_slug: str, skip: int = 0, limit: int = 10) -> List[dict]:
        """Find posts by tag slug (optimized using denormalized tag_slugs field)"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value, "tag_slugs": tag_slug, "deleted_at": None}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return results
    
    async def find_by_tag_ids(self, tag_ids: List[ObjectId], match_all: bool = True, skip: int = 0, limit: int = 10, status: str = None) -> List[dict]:
        """
        Find posts by multiple tag IDs
        Args:
            tag_ids: List of tag IDs to filter by
            match_all: If True, posts must have ALL tags (AND). If False, posts must have ANY tag (OR)
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Optional status filter (e.g., 'published', 'draft')
        """
        query = {"deleted_at": None}
        
        if status:
            query["status"] = status
        
        if match_all:
            # Posts must have ALL specified tags (AND logic)
            query["tag_ids"] = {"$all": tag_ids}
        else:
            # Posts must have ANY of the specified tags (OR logic)
            query["tag_ids"] = {"$in": tag_ids}
        
        cursor = self.collection.find(query).sort("published_at", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return results
    
    async def find_by_tag_names(self, tag_names: List[str], match_all: bool = True, skip: int = 0, limit: int = 10, status: str = None) -> List[dict]:
        """
        Find posts by multiple tag names (optimized using denormalized tag_names field)
        Args:
            tag_names: List of tag names to filter by
            match_all: If True, posts must have ALL tags (AND). If False, posts must have ANY tag (OR)
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Optional status filter (e.g., 'published', 'draft')
        """
        query = {"deleted_at": None}
        
        if status:
            query["status"] = status
        
        if match_all:
            # Posts must have ALL specified tags (AND logic)
            query["tag_names"] = {"$all": tag_names}
        else:
            # Posts must have ANY of the specified tags (OR logic)
            query["tag_names"] = {"$in": tag_names}
        
        cursor = self.collection.find(query).sort("published_at", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return results
    
    async def find_by_tag_slugs(self, tag_slugs: List[str], match_all: bool = True, skip: int = 0, limit: int = 10, status: str = None) -> List[dict]:
        """
        Find posts by multiple tag slugs (optimized using denormalized tag_slugs field)
        Args:
            tag_slugs: List of tag slugs to filter by
            match_all: If True, posts must have ALL tags (AND). If False, posts must have ANY tag (OR)
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Optional status filter (e.g., 'published', 'draft')
        """
        query = {"deleted_at": None}
        
        if status:
            query["status"] = status
        
        if match_all:
            # Posts must have ALL specified tags (AND logic)
            query["tag_slugs"] = {"$all": tag_slugs}
        else:
            # Posts must have ANY of the specified tags (OR logic)
            query["tag_slugs"] = {"$in": tag_slugs}
        
        cursor = self.collection.find(query).sort("published_at", -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return results
    
    async def count_by_tag_ids(self, tag_ids: List[ObjectId], match_all: bool = True, status: str = None) -> int:
        """Count posts by multiple tag IDs"""
        query = {"deleted_at": None}
        
        if status:
            query["status"] = status
        
        if match_all:
            query["tag_ids"] = {"$all": tag_ids}
        else:
            query["tag_ids"] = {"$in": tag_ids}
        
        return await self.collection.count_documents(query)
    
    async def count_by_tag_names(self, tag_names: List[str], match_all: bool = True, status: str = None) -> int:
        """Count posts by multiple tag names"""
        query = {"deleted_at": None}
        
        if status:
            query["status"] = status
        
        if match_all:
            query["tag_names"] = {"$all": tag_names}
        else:
            query["tag_names"] = {"$in": tag_names}
        
        return await self.collection.count_documents(query)
    
    async def count_by_tag_slugs(self, tag_slugs: List[str], match_all: bool = True, status: str = None) -> int:
        """Count posts by multiple tag slugs"""
        query = {"deleted_at": None}
        
        if status:
            query["status"] = status
        
        if match_all:
            query["tag_slugs"] = {"$all": tag_slugs}
        else:
            query["tag_slugs"] = {"$in": tag_slugs}
        
        return await self.collection.count_documents(query)
    
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
    
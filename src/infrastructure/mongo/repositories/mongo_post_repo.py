from typing import List, Optional
from bson import ObjectId
from src.domain.blog.entities.post_entity import Post
from src.domain.blog.repositories.post_repo import PostRepository
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.domain.blog.value_objects.slug import Slug
from src.domain.blog.value_objects.statuses import PostStatus

class MongoPostRepository(PostRepository):
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["posts"]
    async def list_posts(self, skip: int = 0, limit: int = 10):
        cursor = self.db["posts"].find().skip(skip).limit(limit)
        posts = await cursor.to_list(length=limit)
        return [self._to_post_entity(post) for post in posts]
    
    async def create_post(self, post: Post) -> Post:
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
            "category": post.category,
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
    
    async def get_by_id(self, post_id: ObjectId) -> Optional[Post]:
        """Get post by ID"""
        result = await self.collection.find_one({"_id": post_id})
        if not result:
            return None
        return self._to_post_entity(result)
    
    async def get_by_slug(self, slug: Slug) -> Optional[Post]:
        """Get post by slug"""
        result = await self.collection.find_one({"slug": str(slug)})
        if not result:
            return None
        return self._to_post_entity(result)
    
    async def find_published(self, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find published posts"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return [self._to_post_entity(doc) for doc in results]
    
    async def find_by_tag(self, tag: str, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find posts by tag"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value, "tags": tag}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return [self._to_post_entity(doc) for doc in results]
    
    async def delete(self, post_id: ObjectId) -> bool:
        """Delete post"""
        result = await self.collection.delete_one({"_id": post_id})
        return result.deleted_count > 0
    
    async def count_published(self) -> int:
        """Count published posts"""
        return await self.collection.count_documents(
            {"status": PostStatus.PUBLISHED.value}
        )
    
    def _to_post_entity(self, doc: dict) -> Post:
        """Convert MongoDB document to Post entity"""
        # comments = [
        #     Comment(
        #         id=c["_id"],
        #         author_name=c["author_name"],
        #         author_email=c["author_email"],
        #         content=c["content"],
        #         status=CommentStatus(c["status"]),
        #         likes=c.get("likes", 0),
        #         created_at=c["created_at"]
        #     )
        #     for c in doc.get("comments", [])
        # ]
        
        return Post(
            id=doc["_id"],
            slug=Slug(doc["slug"]),
            title=doc["title"],
            content=doc["content"],
            excerpt=doc.get("excerpt"),
            author_name=doc.get("author_name"),
            author_email=doc.get("author_email"),
            status=PostStatus(doc["status"]),
            tags=doc.get("tags", []),
            category=doc.get("category"),
            views_count=doc.get("views_count", 0),
            likes_count=doc.get("likes_count", 0),
            # comments=comments,
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            published_at=doc.get("published_at")
        )

    async def update_post(self, post_id: ObjectId, post_data: dict) -> Optional[Post]:
        """Update post by ID"""
        await self.collection.update_one({"_id": post_id}, {"$set": post_data})
        return await self.get_by_id(post_id)
    
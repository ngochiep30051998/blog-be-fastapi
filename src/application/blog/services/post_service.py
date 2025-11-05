from bson import ObjectId
from src.domain.blog.entities.post_entity import PostEntity
from src.domain.blog.value_objects import Slug
from src.domain.blog.value_objects.statuses import PostStatus
from src.infrastructure.mongo.repositories.mongo_post_repo import MongoPostRepository


class PostService:
    def __init__(self, post_repo: MongoPostRepository):
        self.post_repo = post_repo

    async def get_all_posts(self, skip: int = 0, limit: int = 10):
        posts = await self.post_repo.list_posts(skip=skip, limit=limit)
        total = await self.post_repo.count_posts()
        return posts,total
    
    async def create_post(self, title: str, content: str, slug_str: str,  excerpt: str = None, tags: list = [], category_id: str = None):
        # Create post aggregate
        post = PostEntity(
            id=ObjectId(),
            slug=Slug(slug_str),
            title=title,
            content=content,
            excerpt=excerpt,
            status=PostStatus.DRAFT,
            tags=tags or [],
            category_id=category_id
        )
        saved_post = await self.post_repo.create_post(post)
        return saved_post
    
    async def get_by_id(self, post_id):
        return await self.post_repo.get_by_id(post_id)
    
    async def update_post(self, post_id, post_data):
        return await self.post_repo.update_post(post_id, post_data)
    
    async def delete_post(self, post_id)-> bool: 
        return await self.post_repo.delete(post_id)
    

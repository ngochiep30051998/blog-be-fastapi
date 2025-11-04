from bson import ObjectId
from src.domain.blog.entities.post_entity import Post
from src.domain.blog.repositories.post_repo import PostRepository
from src.domain.blog.value_objects import Slug
from src.domain.blog.value_objects.statuses import PostStatus


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    async def get_all_posts(self, skip: int = 0, limit: int = 10):
        return await self.post_repo.list_posts(skip=skip, limit=limit)
    
    async def create_post(self, title: str, content: str, slug_str: str,  excerpt: str = None, tags: list = [], category: str = None):
        # Create post aggregate
        post = Post(
            id=ObjectId(),
            slug=Slug(slug_str),
            title=title,
            content=content,
            excerpt=excerpt,
            status=PostStatus.DRAFT,
            tags=tags or [],
            category=category
        )
        saved_post = await self.post_repo.create_post(post)
        return saved_post
    
    async def get_post(self, post_id):
        return await self.post_repo.get_post(post_id)
    
    async def update_post(self, post_id, post_data):
        return await self.post_repo.update_post(post_id, post_data)
    
    async def delete_post(self, post_id):
        return await self.post_repo.delete_post(post_id)
    

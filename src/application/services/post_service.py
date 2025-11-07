from bson import ObjectId
from src.core.value_objects.slug import Slug
from src.core.value_objects.statuses import PostStatus
from src.domain.posts.entity import PostEntity
from src.infrastructure.mongo.post_repository_impl import MongoPostRepository
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository

class PostService:
    def __init__(self, post_repo: MongoPostRepository, user_repo: MongoUserRepository):
        self.post_repo = post_repo
        self.user_repo = user_repo

    async def get_all_posts(self, skip: int = 0, limit: int = 10):
        posts = await self.post_repo.list_posts(skip=skip, limit=limit)
        total = await self.post_repo.count_posts()
        return posts,total
    
    async def create_post(self, 
                          title: str, 
                          content: str, 
                          slug_str: str,  
                          excerpt: str = None, 
                          tags: list = [], 
                          category_id: str = None,
                          user_id: str = None
                          ):
        # Create post aggregate
        author = await self.user_repo.get_by_id(user_id)
        post = PostEntity(
            id=ObjectId(),
            slug=Slug(slug_str),
            title=title,
            content=content,
            excerpt=excerpt,
            status=PostStatus.DRAFT,
            tags=tags or [],
            category_id=category_id,
            author_name=author.get("full_name") if author else "Unknown",
            author_email=author.get("email") if author else "Unknown"
        )
        saved_post = await self.post_repo.create_post(post)
        return saved_post
    
    async def get_by_id(self, post_id):
        return await self.post_repo.get_by_id(post_id)
    
    async def update_post(self, post_id, post_data):
        return await self.post_repo.update_post(post_id, post_data)
    
    async def delete_post(self, post_id)-> bool: 
        return await self.post_repo.delete(post_id)
    

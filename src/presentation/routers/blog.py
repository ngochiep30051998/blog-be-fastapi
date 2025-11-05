from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List

from src.application.blog.services.post_service import PostService
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.domain.blog.entities.post_entity import Post

from src.infrastructure.mongo.repositories.mongo_post_repo import MongoPostRepository
from src.presentation.schemas.post_schemas import PostCreateRequest, PostResponse



from ...infrastructure.mongo.database import get_database
router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

async def get_post_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PostService:
    """Dependency: Get post application service"""
    post_repo = MongoPostRepository(db)
    return PostService(post_repo)


    
@router.get("/", response_model=List[PostResponse], summary="Get all blog posts")
async def get_posts(
    service: PostService = Depends(get_post_service)
):
    posts = await service.get_all_posts()
    return posts

@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blog post"
)
async def create_post(
    request: PostCreateRequest,
    service: PostService = Depends(get_post_service)
):
    """Create a new blog post"""
    try:
        post = await service.create_post(
            title=request.title,
            content=request.content,
            slug_str=request.slug,
            excerpt=request.excerpt,
            tags=request.tags,
            category=request.category
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
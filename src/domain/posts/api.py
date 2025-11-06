from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dto.base_dto import BaseResponse
from src.application.dto.post_dto import PostCreateRequest, PostResponse
from src.application.services.post_service import PostService
from src.infrastructure.mongo.post_repository_impl import MongoPostRepository
from ...infrastructure.mongo.database import get_database
router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

async def get_post_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PostService:
    """Dependency: Get post application service"""
    post_repo = MongoPostRepository(db)
    return PostService(post_repo)


    
@router.get("", response_model=BaseResponse[List[PostResponse]], summary="Get all blog posts")
async def get_posts(
    service: PostService = Depends(get_post_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of posts per page")
):
    skip = (page - 1) * page_size
    posts, total = (await service.get_all_posts(skip=skip, limit=page_size))
    return BaseResponse(success=True, data=posts, total=total, page=page, page_size=page_size)

@router.post(
    "",
    response_model=BaseResponse[PostResponse],
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
            category_id=request.category_id
        )
        return BaseResponse(success=True, data=post, message="Post created successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{post_id}",
    response_model=BaseResponse[bool],
    summary="Delete a blog post"
)
async def delete_post(
    post_id: str,
    service: PostService = Depends(get_post_service)
):
    """Delete a blog post"""
    try:
        post = await service.delete_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return BaseResponse(success=True, data=post, message="Post deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get(
    "/{post_id}",
    response_model=BaseResponse[PostResponse],
    summary="Get a blog post by ID"
)
async def get_post(
    post_id: str,
    service: PostService = Depends(get_post_service)
):
    """Get a blog post by ID"""
    post = await service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BaseResponse(success=True, data=post, message="Post retrieved successfully")
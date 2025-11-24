from fastapi import APIRouter, HTTPException, Depends, Query, status,Request
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dependencies.role_checker import RoleChecker
from src.application.dto.base_dto import BaseResponse
from src.application.dto.post_dto import PostCreateRequest, PostUpdateRequest, PostResponse
from src.application.services.post_service import PostService
from src.infrastructure.mongo.post_repository_impl import MongoPostRepository
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from ...infrastructure.mongo.database import get_database
router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

async def get_post_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PostService:
    """Dependency: Get post application service"""
    post_repo = MongoPostRepository(db)
    user_repo = MongoUserRepository(db)
    return PostService(post_repo, user_repo)



@router.get("", 
            response_model=BaseResponse[List[PostResponse]], 
            summary="Get all blog posts", 
            dependencies=[Depends(RoleChecker(allowed_roles=["*"]))]
)
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
    summary="Create a new blog post",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer","user"]))]  # Only admin and writer roles allowed
)
async def create_post(
    post_data: PostCreateRequest,
    request: Request,
    service: PostService = Depends(get_post_service)
):
    """Create a new blog post"""
    # Access request information
    user_id = request.state.user_id
    try:
        post = await service.create_post(
            title=post_data.title,
            content=post_data.content,
            slug_str=post_data.slug,
            excerpt=post_data.excerpt,
            tags=post_data.tags,
            category_id=post_data.category_id,
            user_id=user_id
        )
        return BaseResponse(success=True, data=post, message="Post created successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete(
    "/{post_id}",
    response_model=BaseResponse[bool],
    summary="Delete a blog post",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
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

@router.patch(
    "/{post_id}",
    response_model=BaseResponse[PostResponse],
    summary="Update a blog post",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
)
async def update_post(
    post_id: str,
    post_data: PostUpdateRequest,
    request: Request,
    service: PostService = Depends(get_post_service)
):
    """Update a blog post (partial update)"""
    # Access request information if needed
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    post = await service.update_post(post_id, post_data)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BaseResponse(success=True, data=post, message="Post updated successfully")

@router.patch(
    "/{post_id}/publish",
    response_model=BaseResponse[PostResponse],
    summary="Publish a blog post",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
)
async def publish_post(
    post_id: str,
    service: PostService = Depends(get_post_service)
):
    """Publish a blog post (change status to published)"""
    post = await service.publish_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BaseResponse(success=True, data=post, message="Post published successfully")

@router.patch(
    "/{post_id}/unpublish",
    response_model=BaseResponse[PostResponse],
    summary="Unpublish a blog post",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
)
async def unpublish_post(
    post_id: str,
    service: PostService = Depends(get_post_service)
):
    """Unpublish a blog post (change status back to draft)"""
    post = await service.unpublish_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return BaseResponse(success=True, data=post, message="Post unpublished successfully")
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dto.base_dto import BaseResponse
from src.application.dto.post_dto import PostResponse
from src.application.dto.category_dto import CategoryResponse
from src.application.dto.tag_dto import TagResponse
from src.application.services.post_service import PostService
from src.application.services.category_service import CategoryService
from src.application.services.tag_service import TagService
from src.infrastructure.mongo.post_repository_impl import MongoPostRepository
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from src.infrastructure.mongo.tag_repository_impl import MongoTagRepository
from src.infrastructure.mongo.category_repository_impl import MongoCategoryRepository
from ...infrastructure.mongo.database import get_database

router = APIRouter(prefix="/web", tags=["web-public"])

# Dependencies
async def get_post_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PostService:
    """Dependency: Get post application service"""
    post_repo = MongoPostRepository(db)
    user_repo = MongoUserRepository(db)
    tag_repo = MongoTagRepository(db)
    return PostService(post_repo, user_repo, tag_repo)

async def get_category_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CategoryService:
    """Dependency: Get category application service"""
    category_repo = MongoCategoryRepository(db)
    return CategoryService(category_repo)

async def get_tag_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TagService:
    """Dependency: Get tag application service"""
    tag_repo = MongoTagRepository(db)
    return TagService(tag_repo)


# ==================== POSTS ENDPOINTS ====================

@router.get(
    "/posts",
    response_model=BaseResponse[List[PostResponse]],
    summary="Get all published blog posts (Public)",
    description="Get a paginated list of published blog posts. Only published posts are returned."
)
async def get_published_posts(
    service: PostService = Depends(get_post_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of posts per page"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    tag_ids: Optional[List[str]] = Query(None, description="Filter by tag IDs (comma-separated)"),
    tag_names: Optional[List[str]] = Query(None, description="Filter by tag names (comma-separated)"),
    tag_slugs: Optional[List[str]] = Query(None, description="Filter by tag slugs (comma-separated)"),
    match_all: bool = Query(True, description="If true, posts must have ALL tags (AND). If false, posts must have ANY tag (OR)")
):
    """
    Get all published blog posts with optional filtering
    
    - **category_id**: Filter posts by category ID
    - **tag_ids**: Filter posts by tag IDs (e.g., ?tag_ids=id1&tag_ids=id2)
    - **tag_names**: Filter posts by tag names (e.g., ?tag_names=python&tag_names=fastapi)
    - **tag_slugs**: Filter posts by tag slugs (e.g., ?tag_slugs=python&tag_slugs=fastapi)
    - **match_all**: 
        - `true` (default): Posts must have ALL specified tags (AND logic)
        - `false`: Posts must have ANY of the specified tags (OR logic)
    """
    skip = (page - 1) * page_size
    posts, total = await service.get_published_posts(
        skip=skip,
        limit=page_size,
        category_id=category_id,
        tag_ids=tag_ids,
        tag_names=tag_names,
        tag_slugs=tag_slugs,
        match_all=match_all
    )
    return BaseResponse(success=True, data=posts, total=total, page=page, page_size=page_size)


@router.get(
    "/posts/slug/{slug}",
    response_model=BaseResponse[PostResponse],
    summary="Get a published blog post by slug (Public)",
    description="Get a single published blog post by its slug. Returns 404 if post is not published or not found."
)
async def get_published_post_by_slug(
    slug: str,
    service: PostService = Depends(get_post_service)
):
    """Get a published blog post by slug"""
    post = await service.get_published_post_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Published post not found")
    return BaseResponse(success=True, data=post, message="Post retrieved successfully")


@router.get(
    "/posts/category/{category_id}",
    response_model=BaseResponse[List[PostResponse]],
    summary="Get published posts by category (Public)",
    description="Get all published posts in a specific category"
)
async def get_published_posts_by_category(
    category_id: str,
    service: PostService = Depends(get_post_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of posts per page")
):
    """Get published posts by category ID"""
    skip = (page - 1) * page_size
    posts, total = await service.get_published_posts_by_category(
        category_id=category_id,
        skip=skip,
        limit=page_size
    )
    return BaseResponse(success=True, data=posts, total=total, page=page, page_size=page_size)


@router.get(
    "/posts/tag/{tag_slug}",
    response_model=BaseResponse[List[PostResponse]],
    summary="Get published posts by tag slug (Public)",
    description="Get all published posts with a specific tag"
)
async def get_published_posts_by_tag_slug(
    tag_slug: str,
    service: PostService = Depends(get_post_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of posts per page")
):
    """Get published posts by tag slug"""
    skip = (page - 1) * page_size
    posts, total = await service.get_published_posts_by_tag_slug(
        tag_slug=tag_slug,
        skip=skip,
        limit=page_size
    )
    return BaseResponse(success=True, data=posts, total=total, page=page, page_size=page_size)


# ==================== CATEGORIES ENDPOINTS ====================

@router.get(
    "/categories",
    response_model=BaseResponse[List[CategoryResponse]],
    summary="Get all categories (Public)",
    description="Get a paginated list of all active categories"
)
async def get_categories(
    service: CategoryService = Depends(get_category_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of categories per page")
):
    """Get all categories"""
    skip = (page - 1) * page_size
    categories, total = await service.get_all_categories(skip=skip, limit=page_size)
    return BaseResponse(success=True, data=categories, total=total, page=page, page_size=page_size)


@router.get(
    "/categories/{category_id}",
    response_model=BaseResponse[CategoryResponse],
    summary="Get a category by ID (Public)",
    description="Get a single category by its ID, including all children categories"
)
async def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """Get a category by ID"""
    category = await service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return BaseResponse(success=True, data=category, message="Category retrieved successfully")


# ==================== TAGS ENDPOINTS ====================

@router.get(
    "/tags",
    response_model=BaseResponse[List[TagResponse]],
    summary="Get all tags (Public)",
    description="Get a paginated list of all active tags"
)
async def get_tags(
    service: TagService = Depends(get_tag_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of tags per page")
):
    """Get all tags"""
    skip = (page - 1) * page_size
    tags, total = await service.get_all_tags(skip=skip, limit=page_size)
    return BaseResponse(success=True, data=tags, total=total, page=page, page_size=page_size)


@router.get(
    "/tags/{tag_id}",
    response_model=BaseResponse[TagResponse],
    summary="Get a tag by ID (Public)",
    description="Get a single tag by its ID"
)
async def get_tag(
    tag_id: str,
    service: TagService = Depends(get_tag_service)
):
    """Get a tag by ID"""
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return BaseResponse(success=True, data=tag, message="Tag retrieved successfully")


@router.get(
    "/tags/slug/{slug}",
    response_model=BaseResponse[TagResponse],
    summary="Get a tag by slug (Public)",
    description="Get a single tag by its slug"
)
async def get_tag_by_slug(
    slug: str,
    service: TagService = Depends(get_tag_service)
):
    """Get a tag by slug"""
    tag = await service.get_tag_by_slug(slug)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return BaseResponse(success=True, data=tag, message="Tag retrieved successfully")

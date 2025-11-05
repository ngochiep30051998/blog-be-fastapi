from typing import List
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi import APIRouter, HTTPException, Depends, Query, status
from src.application.blog.services.category_service import CategoryService
from src.infrastructure.mongo.repositories.mongo_category_repo import MongoCategoryRepository
from src.presentation.schemas.base_schemas import BaseResponse
from src.presentation.schemas.category_schema import CategoryCreateRequest, CategoryResponse
from ....infrastructure.mongo.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
router = APIRouter(prefix="/api/v1/categories", tags=["categories"])

async def get_category_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CategoryService:
    """Dependency: Get category application service"""
    category_repo = MongoCategoryRepository(db)
    return CategoryService(category_repo)

@router.get("", response_model=BaseResponse[List[CategoryResponse]], summary="Get all blog categories")
async def get_categories(
    service: CategoryService = Depends(get_category_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of categories per page")
):
    skip = (page - 1) * page_size
    categories, total = (await service.get_all_categories(skip=skip, limit=page_size))
    return BaseResponse(success=True, data=categories, total=total, page=page, page_size=page_size)


@router.post(
    "",
    response_model=BaseResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category"
)
async def create_category(
    request: CategoryCreateRequest,
    service: CategoryService = Depends(get_category_service),
):
    """Create a new category"""
    try:
        category = await service.create_category(
            name=request.name,
            description=request.description,
            slug_str=request.slug,
            parent_id=request.parent_id or None
        )
        return BaseResponse(success=True, data=category, message="category created successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
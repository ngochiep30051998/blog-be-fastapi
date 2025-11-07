from typing import List
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi import APIRouter, HTTPException, Depends, Query, status

from src.application.dependencies.role_checker import RoleChecker
from src.application.dto.base_dto import BaseResponse
from src.application.dto.category_dto import CategoryCreateRequest, CategoryResponse
from src.application.services.category_service import CategoryService
from src.infrastructure.mongo.category_repository_impl import MongoCategoryRepository

from ...infrastructure.mongo.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
router = APIRouter(prefix="/api/v1/categories", tags=["categories"])

async def get_category_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CategoryService:
    """Dependency: Get category application service"""
    category_repo = MongoCategoryRepository(db)
    return CategoryService(category_repo)

@router.get("", 
            response_model=BaseResponse[List[CategoryResponse]], 
            summary="Get all blog categories",
            )
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
    summary="Create a new category",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
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
    
@router.delete(
    "/{category_id}",
    response_model=BaseResponse[bool],
    summary="Delete a category",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
)
async def delete_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
):
    """Delete a category"""
    deleted = await service.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return BaseResponse(success=True, message="Category deleted successfully", data=deleted)

@router.put(
    "/{category_id}",
    response_model=BaseResponse[CategoryResponse],
    summary="Update a category",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]  # Only admin and writer roles allowed
)
async def update_category(
    category_id: str,
    request: CategoryCreateRequest,
    service: CategoryService = Depends(get_category_service),
):
    """Update a category"""
    try:
        updated_category = await service.update_category(
            category_id=category_id,
            name=request.name,
            description=request.description,
            slug_str=request.slug,
            parent_id=request.parent_id or None
        )
        if not updated_category:
            raise HTTPException(status_code=404, detail="Category not found")
        return BaseResponse(success=True, data=updated_category, message="Category updated successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.get(
    "/{category_id}",
    response_model=BaseResponse[CategoryResponse],
    summary="Get a category by ID"
)
async def get_category(
    category_id: str,
    service: CategoryService = Depends(get_category_service),
):
    """Get a category by ID"""
    category = await service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return BaseResponse(success=True, data=category)
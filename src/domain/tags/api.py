from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dependencies.role_checker import RoleChecker
from src.application.dto.base_dto import BaseResponse
from src.application.dto.tag_dto import TagCreateRequest, TagUpdateRequest, TagResponse
from src.application.services.tag_service import TagService
from src.infrastructure.mongo.tag_repository_impl import MongoTagRepository

from ...infrastructure.mongo.database import get_database

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


async def get_tag_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> TagService:
    """Dependency: Get tag application service"""
    tag_repo = MongoTagRepository(db)
    return TagService(tag_repo)


@router.get(
    "",
    response_model=BaseResponse[List[TagResponse]],
    summary="Get all tags",
    dependencies=[Depends(RoleChecker(allowed_roles=["*"]))]
)
async def get_tags(
    service: TagService = Depends(get_tag_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of tags per page")
):
    skip = (page - 1) * page_size
    tags, total = await service.get_all_tags(skip=skip, limit=page_size)
    return BaseResponse(success=True, data=tags, total=total, page=page, page_size=page_size)


@router.post(
    "",
    response_model=BaseResponse[TagResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tag",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]
)
async def create_tag(
    request: TagCreateRequest,
    service: TagService = Depends(get_tag_service),
):
    """Create a new tag"""
    try:
        tag = await service.create_tag(
            name=request.name,
            description=request.description,
            slug_str=request.slug
        )
        return BaseResponse(success=True, data=tag, message="Tag created successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{tag_id}",
    response_model=BaseResponse[TagResponse],
    summary="Get a tag by ID",
    dependencies=[Depends(RoleChecker(allowed_roles=["*"]))]
)
async def get_tag(
    tag_id: str,
    service: TagService = Depends(get_tag_service),
):
    """Get a tag by ID"""
    tag = await service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return BaseResponse(success=True, data=tag)


@router.patch(
    "/{tag_id}",
    response_model=BaseResponse[TagResponse],
    summary="Update a tag",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]
)
async def update_tag(
    tag_id: str,
    request: TagUpdateRequest,
    service: TagService = Depends(get_tag_service),
):
    """Update a tag (partial update)"""
    try:
        updated_tag = await service.update_tag(
            tag_id=tag_id,
            name=request.name,
            description=request.description,
            slug_str=request.slug
        )
        if not updated_tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        return BaseResponse(success=True, data=updated_tag, message="Tag updated successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{tag_id}",
    response_model=BaseResponse[bool],
    summary="Delete a tag",
    dependencies=[Depends(RoleChecker(allowed_roles=["admin", "writer"]))]
)
async def delete_tag(
    tag_id: str,
    service: TagService = Depends(get_tag_service),
):
    """Delete a tag"""
    deleted = await service.delete_tag(tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
    return BaseResponse(success=True, message="Tag deleted successfully", data=deleted)


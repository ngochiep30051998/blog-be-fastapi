from fastapi import APIRouter
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dto.base_dto import BaseResponse
from src.application.dto.user_dto import UserResponse
from src.application.services.user_service import UserService
from src.core.security import get_current_user
from src.infrastructure.mongo.database import get_database
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository

router = APIRouter(prefix="/api/v1/users", tags=["users"])


async def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserService:
    """Dependency: Get user application service"""
    user_repo = MongoUserRepository(db)
    return UserService(user_repo)

@router.get("/profile", summary="Get user profile", response_model=BaseResponse[UserResponse])
async def get_user_profile(
    service: UserService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user profile
    Requires: Bearer token in Authorization header
    """
    user_id = current_user["user_id"]
    print("Current User ID:", user_id)
    user = await service.get_by_id(user_id)
    if not user:
        return BaseResponse(success=False, message="User not found", data=None)
    return BaseResponse(success=True, message="User profile fetched successfully", data=user)

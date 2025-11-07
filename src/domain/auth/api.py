from fastapi import APIRouter
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dependencies.role_checker import RoleChecker
from src.application.dto.auth_dto import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from src.application.dto.base_dto import BaseResponse
from src.application.services.user_service import UserService
from src.infrastructure.mongo.database import get_database
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


async def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserService:
    """Dependency: Get user application service"""
    user_repo = MongoUserRepository(db)
    return UserService(user_repo)

@router.post("/register", 
             summary="Register a new user", 
             response_model=BaseResponse[RegisterResponse],
             dependencies=[Depends(RoleChecker(allowed_roles=["admin"]))]  # Only admin role allowed
             )
async def register_user(
    request: RegisterRequest,
    service: UserService = Depends(get_user_service),
):
    """Register a new user"""
    access_token = await service.register_user(request.full_name, request.email, request.password, request.date_of_birth)
    res = RegisterResponse(access_token=access_token, token_type="bearer")
    print("Register a new user", res)
    return BaseResponse(success=True, data=res)

@router.post("/login", summary="User login", response_model=BaseResponse[LoginResponse])
async def login_user(
    request: LoginRequest,
    service: UserService = Depends(get_user_service)
):
    """User login"""
    user = await service.authenticate_user(request.email, request.password)
    if not user:
        return BaseResponse[LoginResponse](success=False, message="Invalid email or password", data=None)
    access_token = service.create_access_token(data={"sub": str(user["_id"]), "role": user["role"]})
    return BaseResponse[LoginResponse](success=True, data=LoginResponse(access_token=access_token, token_type="bearer"))

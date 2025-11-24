from fastapi import APIRouter, Body, Request, HTTPException, status
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.dependencies.role_checker import RoleChecker
from src.application.dto.auth_dto import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from src.application.dto.base_dto import BaseResponse
from src.application.services.user_service import UserService
from src.config import settings
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
    access_token = await service.register_user(request.full_name, request.email, request.password, request.date_of_birth, request.role)
    res = RegisterResponse(access_token=access_token, token_type="bearer")
    return BaseResponse(success=True, data=res)

@router.post("/login", summary="User login", response_model=BaseResponse[LoginResponse])
async def login_user(
    request: LoginRequest = Body(..., example={
                        "email": settings.ENVIRONMENT == "development" and settings.DEFAULT_USER_EMAIL or "user@example.com",
                        "password": settings.ENVIRONMENT == "development" and settings.DEFAULT_USER_PASSWORD or "password"
    }),
    service: UserService = Depends(get_user_service)
):
    """User login - creates a new session and invalidates any existing session"""
    try:
        access_token = await service.login_user(request.email, request.password)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        return BaseResponse[LoginResponse](success=True, data=LoginResponse(access_token=access_token, token_type="bearer"))
    except ValueError as e:
        # User is locked - raise 401 Unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout", summary="User logout", response_model=BaseResponse[dict])
async def logout_user(
    request: Request,
    service: UserService = Depends(get_user_service)
):
    """User logout - invalidates the current session token"""
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return BaseResponse(success=False, message="Authorization header missing", data=None)
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return BaseResponse(success=False, message="Invalid authentication scheme", data=None)
        
        # Invalidate the token
        await service.session_service.invalidate_token(token)
        return BaseResponse(success=True, message="Logged out successfully", data={})
    except ValueError:
        return BaseResponse(success=False, message="Invalid Authorization header format", data=None)

from fastapi import APIRouter, Request, HTTPException, Query, status
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from bson import ObjectId

from src.application.dependencies.role_checker import RoleChecker
from src.application.dto.base_dto import BaseResponse
from src.application.dto.user_dto import UserResponse, UserUpdateRequest, UserLockRequest, ChangePasswordRequest
from src.application.services.user_service import UserService
from src.application.services.audit_service import AuditService
from src.infrastructure.mongo.database import get_database
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from src.infrastructure.mongo.audit_repository_impl import MongoAuditLogRepository
from src.core.role import UserRole

router = APIRouter(prefix="/api/v1/users", tags=["users"])


async def get_user_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UserService:
    """Dependency: Get user application service"""
    user_repo = MongoUserRepository(db)
    return UserService(user_repo)

async def get_audit_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AuditService:
    """Dependency: Get audit service"""
    audit_repo = MongoAuditLogRepository(db)
    return AuditService(audit_repo)

@router.get("/profile", summary="Get user profile", response_model=BaseResponse[UserResponse])
async def get_user_profile(
    request: Request,
    service: UserService = Depends(get_user_service),
):
    """
    Get current user profile
    Requires: Bearer token in Authorization header
    """
    user_id = request.state.user_id
    user = await service.get_by_id(user_id)
    if not user:
        return BaseResponse(success=False, message="User not found", data=None)
    # Remove password_hash if present
    user.pop("password_hash", None)
    return BaseResponse(success=True, message="User profile fetched successfully", data=user)


@router.get("", 
            summary="List all users", 
            response_model=BaseResponse[List[UserResponse]],
            dependencies=[Depends(RoleChecker(allowed_roles=["admin"]))])
async def list_users(
    request: Request,
    service: UserService = Depends(get_user_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of users per page")
):
    """
    List all users
    Requires: Admin role
    """
    skip = (page - 1) * page_size
    users = await service.list_users(skip, page_size)
    return BaseResponse(success=True, data=users, total=len(users), page=page, page_size=page_size)


@router.patch("/{user_id}", 
            summary="Update user", 
            response_model=BaseResponse[UserResponse],
            dependencies=[Depends(RoleChecker(allowed_roles=["*"]))])
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
):
    """
    Update user information
    - Admin can update any user
    - Non-admin can only update themselves
    """
    current_user_id = request.state.user_id
    current_user_role = request.state.user_payload.get("role")
    
    # Check if user exists
    target_user = await service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Authorization check: non-admin can only update themselves
    if current_user_role != "admin" and current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    # Non-admin cannot update role
    if current_user_role != "admin" and update_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your role"
        )
    
    # Prepare update data
    update_dict = {}
    if update_data.full_name is not None:
        update_dict["full_name"] = update_data.full_name
    if update_data.email is not None:
        update_dict["email"] = update_data.email
    if update_data.date_of_birth is not None:
        update_dict["date_of_birth"] = update_data.date_of_birth
    if update_data.role is not None and current_user_role == "admin":
        update_dict["role"] = update_data.role.value
    
    # Update user
    updated_user = await service.update_user(user_id, update_dict)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    
    return BaseResponse(success=True, message="User updated successfully", data=updated_user)


@router.patch("/{user_id}/lock", 
              summary="Lock or unlock user", 
              response_model=BaseResponse[UserResponse],
              dependencies=[Depends(RoleChecker(allowed_roles=["admin"]))])
async def lock_user(
    user_id: str,
    lock_data: UserLockRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
):
    """
    Lock or unlock a user
    Requires: Admin role
    """
    # Check if user exists
    target_user = await service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Lock/unlock user
    updated_user = await service.lock_user(user_id, lock_data.locked)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user lock status"
        )
    
    action = "locked" if lock_data.locked else "unlocked"
    return BaseResponse(success=True, message=f"User {action} successfully", data=updated_user)


@router.post("/{user_id}/unlock", 
              summary="Unlock user account", 
              response_model=BaseResponse[UserResponse],
              dependencies=[Depends(RoleChecker(allowed_roles=["admin"]))])
async def unlock_user(
    user_id: str,
    request: Request,
    service: UserService = Depends(get_user_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Unlock a user account (admin only).
    Resets all lockout-related fields: locked, failed_attempts, locked_until.
    This action is logged for audit purposes.
    """
    # Get admin user info for audit logging
    admin_user_id = request.state.user_id
    admin_user = await service.get_by_id(admin_user_id)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found"
        )
    
    # Check if target user exists
    target_user = await service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Unlock user (resets locked, failed_attempts, locked_until)
    updated_user = await service.unlock_user(user_id)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock user"
        )
    
    # Log the unlock action for audit purposes
    await audit_service.log_admin_action(
        action="unlock_user",
        admin_user_id=admin_user_id,
        admin_user_email=admin_user.get("email", "unknown"),
        target_user_id=user_id,
        target_user_email=target_user.get("email", "unknown"),
        details={
            "previous_locked_status": target_user.get("locked", False),
            "previous_failed_attempts": target_user.get("failed_attempts", 0),
            "previous_locked_until": str(target_user.get("locked_until")) if target_user.get("locked_until") else None
        }
    )
    
    return BaseResponse(success=True, message="User unlocked successfully", data=updated_user)


@router.patch("/{user_id}/change-password", 
              summary="Change user password", 
              response_model=BaseResponse[dict],
              dependencies=[Depends(RoleChecker(allowed_roles=["*"]))])
async def change_password(
    user_id: str,
    password_data: ChangePasswordRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
):
    """
    Change user password
    - Admin can change any user's password
    - Non-admin can only change their own password
    - Requires old password for verification
    - All existing sessions will be invalidated after password change
    """
    current_user_id = request.state.user_id
    current_user_role = request.state.user_payload.get("role")
    
    # Check if user exists
    target_user = await service.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Authorization check: non-admin can only change their own password
    if current_user_role != "admin" and current_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )
    
    try:
        # Change password (this will also invalidate all sessions)
        await service.change_password(user_id, password_data.old_password, password_data.new_password)
        return BaseResponse(success=True, message="Password changed successfully. Please login again.", data={})
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

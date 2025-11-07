from typing import List
from fastapi import Depends, HTTPException, Request, status
from fastapi import security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from src.config import settings
security = HTTPBearer()

def get_user_payload(request: Request) -> dict:
    """Extract user payload from request state set by AuthMiddleware"""
    return request.state.user_payload
class RoleChecker:
    """Dependency check role of user"""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: dict = Depends(get_user_payload)):
        if "*" in self.allowed_roles:
            return current_user  # Allow all roles
        if current_user["role"] not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with role '{current_user['role']}' is not authorized to access this resource"
            )
        return current_user
    

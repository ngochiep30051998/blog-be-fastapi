from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from src.application.dto.user_dto import UserResponse
from src.config import settings
from src.core.role import UserRole
from src.core.value_objects.email import Email

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: str 
    password: str 

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    date_of_birth: Optional[str] = None
    role: Optional[UserRole] = None
class RegisterResponse(BaseModel):
    access_token: str
    token_type: str
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
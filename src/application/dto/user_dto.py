from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

from src.core.value_objects.email import Email
from src.core.role import UserRole
from src.utils.py_object_id import PyObjectId


class UserResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={PyObjectId: str, ObjectId: str, Email: str},
    )
    id: PyObjectId = Field(..., alias="_id") 
    full_name: str
    email: str
    date_of_birth: datetime | None = None
    role: str
    created_at: datetime
    updated_at: datetime
    locked: bool = False


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    role: Optional[UserRole] = None


class UserLockRequest(BaseModel):
    locked: bool


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
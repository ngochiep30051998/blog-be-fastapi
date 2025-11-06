from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from src.core.role import UserRole
from src.utils.py_object_id import PyObjectId


class UserEntity(BaseModel):
    """User aggregate root"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    full_name: str
    email: str
    password_hash: str
    role: UserRole
    date_of_birth: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
    class Config:
        validate_by_name = True
        json_encoders = {
            PyObjectId: str
        }
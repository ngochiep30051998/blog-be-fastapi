from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from src.utils.py_object_id import PyObjectId
from src.core.role import UserRole


class AuditLogEntity(BaseModel):
    """Audit log entity for tracking admin actions"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    action: str  # e.g., "unlock_user", "lock_user", "delete_user"
    admin_user_id: str  # ID of the admin who performed the action
    admin_user_email: str  # Email of the admin for easier tracking
    target_user_id: Optional[str] = None  # ID of the user affected by the action
    target_user_email: Optional[str] = None  # Email of the target user
    details: Optional[dict] = None  # Additional details about the action
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        validate_by_name = True
        json_encoders = {
            PyObjectId: str
        }


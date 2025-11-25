from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from src.core.value_objects.slug import Slug
from src.utils.py_object_id import PyObjectId


class TagEntity(BaseModel):
    """Tag aggregate root"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    slug: Slug
    description: Optional[str] = None
    usage_count: int = 0  # Track how many posts use this tag
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    class Config:
        validate_by_name = True
        json_encoders = {
            ObjectId: str
        }


# class use for create and update tag
class TagCreate(BaseModel):
    name: str
    description: Optional[str] = None


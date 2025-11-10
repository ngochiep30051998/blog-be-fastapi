from dataclasses import dataclass, field
from datetime import datetime,timezone
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from src.utils.py_object_id import PyObjectId


class FileEntity(BaseModel):
    """File aggregate root"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: Optional[str] = None
    cloudinary_url: Optional[str] = None
    mime_type: str
    cloudinary_id: Optional[str] = None
    uploaded_by: Optional[PyObjectId] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
    class Config:
        validate_by_name = True
        json_encoders = {
            ObjectId: str
        }
# class use for create and update category
class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[PyObjectId] = None
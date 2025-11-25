from datetime import datetime,timezone
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from src.core.value_objects.slug import Slug
from src.core.value_objects.statuses import PostStatus
from src.utils.py_object_id import PyObjectId

class PostEntity(BaseModel):
    """Post aggregate root"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    slug: Slug
    title: str
    content: str
    excerpt: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    tags: List[str] = Field(default_factory=list)
    category_id: Optional[PyObjectId] = None
    views_count: int = 0
    likes_count: int = 0
    thumbnail: Optional[str] = None
    banner: Optional[str] = None
    # comments: List[Comment] = field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        validate_by_name = True
        json_encoders = {
            ObjectId: str
        }

#  class use for create and update post
class PostCreate(BaseModel):
    title: str
    content: str
    category_id: PyObjectId
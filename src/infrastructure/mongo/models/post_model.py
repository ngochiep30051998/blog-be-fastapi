from datetime import datetime,timezone
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

from src.utils.py_object_id import PyObjectId


class PostModel(BaseModel):
    """Pydantic model for Post in MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    status: str = "draft"
    tags: List[str] = []
    category_id: Optional[ObjectId] = None
    views_count: int = 0
    likes_count: int = 0
    # comments: List[CommentModel] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None
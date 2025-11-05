from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Any, Optional, List
from datetime import datetime

from src.domain.blog.value_objects.slug import Slug
from src.utils.py_object_id import PyObjectId

class PostCreateRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str},
    )
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    slug: str = Field(..., pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = []
    category_id: Optional[str] = None

    @model_validator(mode="before")
    def convert_objectid(cls, values: Any) -> Any:
        if hasattr(values, 'category_id') and isinstance(values.category_id, ObjectId):
            values.category_id = str(values.category_id)
        return values


class PostResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={PyObjectId: str, ObjectId: str, Slug: str},
    )
    id: PyObjectId = Field(..., alias="_id") 
    slug: Slug
    title: str
    content: str
    excerpt: Optional[str] = None
    author_name: Optional[str] = None
    status: str
    tags: List[str]
    category_id: Optional[PyObjectId] = None
    views_count: int
    likes_count: int
    # comments: List[CommentResponse] = []
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @model_validator(mode="before")
    def convert_objectid(cls, values: Any) -> Any:
        # Đổi slug thành string nếu cần
        if 'slug' in values and not isinstance(values['slug'], str):
            values['slug'] = str(values['slug'])
        # ObjectId trong _id (nhờ alias, trường id sẽ nhận _id)
        if '_id' in values and isinstance(values['_id'], ObjectId):
            values['_id'] = str(values['_id'])
        # ObjectId trong _id (nhờ alias, trường id sẽ nhận _id)
        if 'category_id' in values and isinstance(values['category_id'], ObjectId):
            values['category_id'] = str(values['category_id'])
        return values
    @field_validator('slug', mode='before')
    def validate_slug(cls, v):
        if isinstance(v, str):
            return Slug(value=v)
        return v

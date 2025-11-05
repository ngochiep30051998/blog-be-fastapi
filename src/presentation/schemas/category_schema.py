from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime

from src.domain.blog.value_objects.slug import Slug
from src.utils.py_object_id import PyObjectId

class CategoryCreateRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str},
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    slug: Optional[str] = None

class CategoryResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={PyObjectId: str, ObjectId: str, Slug: str},
    )
    id: PyObjectId = Field(..., alias="_id")  # alias để map chính xác _id MongoDB
    name: str
    description: Optional[str] = None
    slug: Slug
    parent_id: Optional[PyObjectId] = None
    path: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @model_validator(mode="before")
    def convert_objectid(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Đổi slug thành string nếu cần
            if 'slug' in values and not isinstance(values['slug'], str):
                values['slug'] = str(values['slug'])
            # ObjectId trong _id (nhờ alias, trường id sẽ nhận _id)
            if '_id' in values and isinstance(values['_id'], ObjectId):
                values['_id'] = str(values['_id'])
            if 'parent_id' in values and isinstance(values['parent_id'], ObjectId):
                values['parent_id'] = str(values['parent_id'])
        return values

    @field_validator('slug', mode='before')
    def validate_slug(cls, v):
        if isinstance(v, str):
            return Slug(value=v)
        return v
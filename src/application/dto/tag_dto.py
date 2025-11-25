from typing import Any, List, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime

from src.core.value_objects.slug import Slug
from src.utils.py_object_id import PyObjectId


class TagCreateRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str},
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = None


class TagUpdateRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str},
    )
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = None


class TagResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={PyObjectId: str, ObjectId: str, Slug: str},
    )
    id: PyObjectId = Field(..., alias="_id")
    name: str
    slug: Slug
    description: Optional[str] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    def convert_objectid(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if 'slug' in values and not isinstance(values['slug'], str):
                values['slug'] = str(values['slug'])
            if '_id' in values and isinstance(values['_id'], ObjectId):
                values['_id'] = str(values['_id'])
        return values

    @field_validator('slug', mode='before')
    def validate_slug(cls, v):
        if isinstance(v, str):
            return Slug(value=v)
        return v


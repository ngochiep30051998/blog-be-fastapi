from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, model_validator

from src.utils.py_object_id import PyObjectId


class FileCreateRequest(BaseModel):
    name: Optional[str] = None
    cloudinary_url: Optional[str] = None
    mime_type: str
    alt: Optional[str] = None

class FileResponse(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: Optional[str] = None
    cloudinary_url: Optional[str] = None
    mime_type: str
    alt: Optional[str] = None
    uploaded_by: Optional[PyObjectId] = None

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
    

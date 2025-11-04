from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    slug: str = Field(..., pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None

class PostResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
    
    id: str = Field(alias="_id")
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author_name: Optional[str] = None
    status: str
    tags: List[str]
    category: Optional[str] = None
    views_count: int
    likes_count: int
    # comments: List[CommentResponse] = []
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
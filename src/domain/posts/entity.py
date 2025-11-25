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
    tag_ids: List[PyObjectId] = Field(default_factory=list)
    tag_names: List[str] = Field(default_factory=list)  # Denormalized for faster reads
    tag_slugs: List[str] = Field(default_factory=list)  # Denormalized tag slugs for faster reads
    category_id: Optional[PyObjectId] = None
    views_count: int = 0
    likes_count: int = 0
    thumbnail: Optional[str] = None
    banner: Optional[str] = None
    # SEO fields
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: List[str] = Field(default_factory=list)
    meta_robots: Optional[str] = None  # e.g., "index, follow", "noindex, nofollow"
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: Optional[str] = None  # e.g., "article", "website"
    twitter_card: Optional[str] = None  # e.g., "summary_large_image", "summary"
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None
    canonical_url: Optional[str] = None
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
    # SEO fields (all optional)
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: List[str] = Field(default_factory=list)
    meta_robots: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: Optional[str] = None
    twitter_card: Optional[str] = None
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None
    canonical_url: Optional[str] = None
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Any, Optional, List, Union
from datetime import datetime
from src.application.dto.category_dto import CategoryResponse
from src.application.dto.tag_dto import TagResponse
from src.core.value_objects.slug import Slug
from src.utils.py_object_id import PyObjectId


class TagInput(BaseModel):
    """Tag input model that accepts either id, name, or both"""
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
    id: Optional[str] = None
    name: Optional[str] = None
    
    @model_validator(mode="before")
    @classmethod
    def validate_tag_input(cls, values):
        """Ensure at least id or name is provided"""
        if isinstance(values, dict):
            if not values.get('id') and not values.get('name'):
                raise ValueError("Either 'id' or 'name' must be provided for a tag")
        return values


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
    tags: Optional[List[TagInput]] = Field(default_factory=list, description="List of tags with id and/or name")
    category_id: Optional[str] = None
    thumbnail: Optional[str] = None
    banner: Optional[str] = None
    # SEO fields
    meta_title: Optional[str] = Field(None, max_length=60, description="Meta title for SEO (recommended: 50-60 characters)")
    meta_description: Optional[str] = Field(None, max_length=160, description="Meta description for SEO (recommended: 150-160 characters)")
    meta_keywords: Optional[List[str]] = Field(None, description="Meta keywords for SEO")
    meta_robots: Optional[str] = Field(None, description="Meta robots directive (e.g., 'index, follow', 'noindex, nofollow')")
    og_title: Optional[str] = Field(None, description="Open Graph title for social media sharing")
    og_description: Optional[str] = Field(None, description="Open Graph description for social media sharing")
    og_image: Optional[str] = Field(None, description="Open Graph image URL for social media sharing")
    og_type: Optional[str] = Field(None, description="Open Graph type (e.g., 'article', 'website')")
    twitter_card: Optional[str] = Field(None, description="Twitter card type (e.g., 'summary_large_image', 'summary')")
    twitter_title: Optional[str] = Field(None, description="Twitter title for social media sharing")
    twitter_description: Optional[str] = Field(None, description="Twitter description for social media sharing")
    twitter_image: Optional[str] = Field(None, description="Twitter image URL for social media sharing")
    canonical_url: Optional[str] = Field(None, description="Canonical URL for SEO")
    @model_validator(mode="before")
    def convert_objectid(cls, values: Any) -> Any:
        if hasattr(values, 'category_id') and isinstance(values.category_id, ObjectId):
            values.category_id = str(values.category_id)
        return values


class PostUpdateRequest(BaseModel):
    """DTO for partial post updates (PATCH) - all fields are optional"""
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str},
    )
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    slug: Optional[str] = Field(None, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    excerpt: Optional[str] = None
    tags: Optional[List[TagInput]] = Field(None, description="List of tags with id and/or name")
    category_id: Optional[str] = None
    thumbnail: Optional[str] = None
    banner: Optional[str] = None
    # SEO fields
    meta_title: Optional[str] = Field(None, max_length=60, description="Meta title for SEO (recommended: 50-60 characters)")
    meta_description: Optional[str] = Field(None, max_length=160, description="Meta description for SEO (recommended: 150-160 characters)")
    meta_keywords: Optional[List[str]] = Field(None, description="Meta keywords for SEO")
    meta_robots: Optional[str] = Field(None, description="Meta robots directive (e.g., 'index, follow', 'noindex, nofollow')")
    og_title: Optional[str] = Field(None, description="Open Graph title for social media sharing")
    og_description: Optional[str] = Field(None, description="Open Graph description for social media sharing")
    og_image: Optional[str] = Field(None, description="Open Graph image URL for social media sharing")
    og_type: Optional[str] = Field(None, description="Open Graph type (e.g., 'article', 'website')")
    twitter_card: Optional[str] = Field(None, description="Twitter card type (e.g., 'summary_large_image', 'summary')")
    twitter_title: Optional[str] = Field(None, description="Twitter title for social media sharing")
    twitter_description: Optional[str] = Field(None, description="Twitter description for social media sharing")
    twitter_image: Optional[str] = Field(None, description="Twitter image URL for social media sharing")
    canonical_url: Optional[str] = Field(None, description="Canonical URL for SEO")
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
    author_email: Optional[str] = None
    status: str
    tags: List[TagResponse] = Field(default_factory=list)  # Full tag objects with id, name, slug, etc.
    category: Optional[CategoryResponse] = None  # change category_id to object
    views_count: int
    likes_count: int
    thumbnail: Optional[str] = None
    banner: Optional[str] = None
    # SEO fields
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
    # comments: List[CommentResponse] = []
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


    @model_validator(mode="before")
    def convert_objectid(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if '_id' in values:
                values['_id'] = str(values['_id'])
            if 'slug' in values and not isinstance(values['slug'], str):
                values['slug'] = str(values['slug'])
            if 'category' in values and values['category']:
                # Convert ObjectId in category
                cat = values['category']
                if '_id' in cat and isinstance(cat['_id'], ObjectId):
                    cat['_id'] = str(cat['_id'])
                if 'parent_id' in cat and isinstance(cat['parent_id'], ObjectId):
                    cat['parent_id'] = str(cat['parent_id'])
                values['category'] = cat
            # Handle tags array from $lookup
            if 'tags' in values and values['tags']:
                tags = values['tags']
                if isinstance(tags, list):
                    for tag in tags:
                        if isinstance(tag, dict) and '_id' in tag and isinstance(tag['_id'], ObjectId):
                            tag['_id'] = str(tag['_id'])
                        if isinstance(tag, dict) and 'slug' in tag and not isinstance(tag['slug'], str):
                            tag['slug'] = str(tag['slug'])
            # Remove denormalized tag fields from response (they're for internal querying only)
            # Clients should use the 'tags' field which contains full tag objects
            values.pop('tag_ids', None)
            values.pop('tag_names', None)
            values.pop('tag_slugs', None)
        return values
    @field_validator('slug', mode='before')
    def validate_slug(cls, v):
        if isinstance(v, str):
            return Slug(value=v)
        return v

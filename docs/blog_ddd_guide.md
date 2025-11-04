# Personal Blog with Domain-Driven Design, FastAPI & MongoDB

A comprehensive step-by-step guide to build a production-ready backend blog API using FastAPI, MongoDB, Docker Compose, and clean DDD architecture.

---

## Table of Contents

1. Database Design & Schema
2. Project Structure
3. DDD Building Blocks
4. Implementation Guide
5. Docker Compose Setup
6. Testing & Deployment

---

## 1. Database Design & Schema

### 1.1 MongoDB Collections Structure

For a blog application, we'll use an embedded document model for optimal MongoDB performance:

```javascript
// posts collection
{
  _id: ObjectId,
  slug: String (unique index),
  title: String (required),
  content: String (required),
  excerpt: String,
  author: {
    id: ObjectId (reference to users),
    name: String,
    email: String
  },
  status: String (enum: draft, published),
  tags: [String],
  category: String,
  views_count: Number (default: 0),
  likes_count: Number (default: 0),
  comments: [
    {
      _id: ObjectId,
      author: {
        name: String,
        email: String
      },
      content: String,
      status: String (enum: approved, pending, spam),
      created_at: DateTime,
      likes: Number
    }
  ],
  created_at: DateTime (default: now),
  updated_at: DateTime (default: now),
  published_at: DateTime (nullable)
}

// tags collection
{
  _id: ObjectId,
  name: String (unique),
  slug: String (unique, index),
  description: String,
  posts_count: Number (default: 0),
  created_at: DateTime
}

// authors collection
{
  _id: ObjectId,
  email: String (unique, index),
  username: String (unique),
  name: String,
  bio: String,
  avatar_url: String,
  created_at: DateTime,
  updated_at: DateTime
}

// categories collection
{
  _id: ObjectId,
  name: String (unique),
  slug: String (unique, index),
  description: String,
  posts_count: Number (default: 0),
  created_at: DateTime
}
```

### 1.2 MongoDB Design Decisions

**Why Embedded Comments?**
- Fast retrieval: Get post + all comments in single query
- Maintains transactional consistency within aggregate
- Simpler queries for read-heavy blog operations
- Easier to enforce invariants within post aggregate

**Denormalization (author, tags in posts)**
- Improves read performance (single query for complete post)
- Tags and authors info is relatively static
- Update operations are infrequent

**Indexes for Performance**
- `slug` (unique) - fast lookups by post URL
- `status` + `published_at` - efficient queries for published posts
- `created_at` - sort posts by recency
- `tags` - filter by tags
- `author.id` - find author's posts

---

## 2. Project Structure

```
personal-blog/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   └── constants.py
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── blog/
│   │   │   ├── __init__.py
│   │   │   ├── entities.py (Post, Comment, Author, Tag, Category)
│   │   │   ├── value_objects.py (Slug, Email, PostStatus, etc.)
│   │   │   ├── repositories.py (abstract interfaces)
│   │   │   └── exceptions.py (domain exceptions)
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   ├── blog/
│   │   │   ├── __init__.py
│   │   │   ├── services.py (PostService, CommentService, etc.)
│   │   │   ├── dto.py (Data Transfer Objects)
│   │   │   └── commands/ (optional: CQRS pattern)
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── mongo/
│   │   │   ├── __init__.py
│   │   │   ├── database.py (connection setup)
│   │   │   ├── repositories.py (concrete implementations)
│   │   │   └── models.py (Pydantic models for MongoDB)
│   │   └── dependencies.py (FastAPI dependencies)
│   │
│   ├── presentation/
│   │   ├── __init__.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── blog.py (posts routes)
│   │   │   ├── comments.py (comments routes)
│   │   │   └── tags.py (tags routes)
│   │   └── schemas.py (request/response models)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── slugify.py
│       └── validators.py
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    └── integration/
```

---

## 3. DDD Building Blocks

### 3.1 Value Objects

Value objects are immutable, self-validating objects that don't have identity.

```python
# src/domain/blog/value_objects.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum
import re

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

class CommentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SPAM = "spam"

@dataclass(frozen=True)
class Email:
    """Email value object with validation"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email: {self.value}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class Slug:
    """URL-friendly slug value object"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_slug(self.value):
            raise ValueError(f"Invalid slug: {self.value}")
    
    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return re.match(pattern, slug) is not None
    
    def __str__(self) -> str:
        return self.value
```

### 3.2 Entities

Entities have identity and lifecycle. They contain both data and behavior.

```python
# src/domain/blog/entities.py

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .value_objects import Email, Slug, PostStatus, CommentStatus

@dataclass
class Author:
    """Author entity (aggregate root)"""
    id: ObjectId
    email: Email
    username: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __eq__(self, other):
        return isinstance(other, Author) and self.id == other.id
    
    def __hash__(self):
        return hash(self.id)

@dataclass
class Comment:
    """Comment value object embedded in Post"""
    id: ObjectId = field(default_factory=ObjectId)
    author_name: str
    author_email: str
    content: str
    status: CommentStatus = CommentStatus.PENDING
    likes: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def approve(self):
        """Business rule: approve comment"""
        if self.status != CommentStatus.PENDING:
            raise ValueError("Only pending comments can be approved")
        self.status = CommentStatus.APPROVED
    
    def mark_as_spam(self):
        """Business rule: mark as spam"""
        self.status = CommentStatus.SPAM
    
    def add_like(self):
        """Business rule: increment likes"""
        self.likes += 1

@dataclass
class Post:
    """Post aggregate root"""
    id: ObjectId
    slug: Slug
    title: str
    content: str
    excerpt: Optional[str] = None
    author_id: Optional[ObjectId] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    views_count: int = 0
    likes_count: int = 0
    comments: List[Comment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    def __eq__(self, other):
        return isinstance(other, Post) and self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    # Business rules (invariants)
    def publish(self):
        """Business rule: Post can only be published from draft"""
        if self.status == PostStatus.PUBLISHED:
            raise ValueError("Post is already published")
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.utcnow()
    
    def add_comment(self, comment: Comment) -> None:
        """Business rule: Add comment to post"""
        if self.status != PostStatus.PUBLISHED:
            raise ValueError("Cannot add comments to unpublished posts")
        if comment.status not in [CommentStatus.PENDING, CommentStatus.APPROVED]:
            raise ValueError("Invalid comment status for new comments")
        self.comments.append(comment)
    
    def record_view(self) -> None:
        """Business rule: Increment view count"""
        self.views_count += 1
    
    def like(self) -> None:
        """Business rule: Like post"""
        self.likes_count += 1
    
    def update_content(self, title: str, content: str, excerpt: Optional[str] = None):
        """Business rule: Update post content"""
        if self.status == PostStatus.PUBLISHED and self.published_at:
            # Allow updates but track the change
            pass
        self.title = title
        self.content = content
        if excerpt:
            self.excerpt = excerpt
        self.updated_at = datetime.utcnow()
```

### 3.3 Repositories (Interfaces)

Repositories are abstractions for persistence.

```python
# src/domain/blog/repositories.py

from abc import ABC, abstractmethod
from typing import List, Optional
from bson import ObjectId
from .entities import Post, Author, Comment
from .value_objects import Slug

class PostRepository(ABC):
    """Post repository interface"""
    
    @abstractmethod
    async def save(self, post: Post) -> Post:
        """Save post to database"""
        pass
    
    @abstractmethod
    async def get_by_id(self, post_id: ObjectId) -> Optional[Post]:
        """Get post by ID"""
        pass
    
    @abstractmethod
    async def get_by_slug(self, slug: Slug) -> Optional[Post]:
        """Get post by slug"""
        pass
    
    @abstractmethod
    async def find_published(self, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find all published posts with pagination"""
        pass
    
    @abstractmethod
    async def find_by_tag(self, tag: str, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find posts by tag"""
        pass
    
    @abstractmethod
    async def delete(self, post_id: ObjectId) -> bool:
        """Delete post"""
        pass
    
    @abstractmethod
    async def count_published(self) -> int:
        """Count published posts"""
        pass

class AuthorRepository(ABC):
    """Author repository interface"""
    
    @abstractmethod
    async def save(self, author: Author) -> Author:
        """Save author"""
        pass
    
    @abstractmethod
    async def get_by_id(self, author_id: ObjectId) -> Optional[Author]:
        """Get author by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Author]:
        """Get author by email"""
        pass
```

### 3.4 Application Services

Services orchestrate use cases and coordinate between domain and infrastructure layers.

```python
# src/application/blog/services.py

from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from ...domain.blog.entities import Post, Author, Comment
from ...domain.blog.repositories import PostRepository, AuthorRepository
from ...domain.blog.value_objects import Slug, Email, PostStatus, CommentStatus

class PostApplicationService:
    """Post application service - use cases for posts"""
    
    def __init__(self, post_repo: PostRepository, author_repo: AuthorRepository):
        self.post_repo = post_repo
        self.author_repo = author_repo
    
    async def create_post(
        self,
        title: str,
        content: str,
        slug_str: str,
        author_id: ObjectId,
        excerpt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> Post:
        """Use case: Create a new blog post"""
        
        # Create value objects with validation
        slug = Slug(slug_str)
        
        # Get author
        author = await self.author_repo.get_by_id(author_id)
        if not author:
            raise ValueError(f"Author {author_id} not found")
        
        # Create post aggregate
        post = Post(
            id=ObjectId(),
            slug=slug,
            title=title,
            content=content,
            excerpt=excerpt,
            author_id=author_id,
            author_name=author.name,
            author_email=str(author.email),
            status=PostStatus.DRAFT,
            tags=tags or [],
            category=category
        )
        
        # Save to repository
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def publish_post(self, post_id: ObjectId) -> Post:
        """Use case: Publish a draft post"""
        
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")
        
        # Enforce business rule
        post.publish()
        
        # Persist changes
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def get_published_posts(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Post], int]:
        """Use case: Retrieve published posts"""
        
        posts = await self.post_repo.find_published(skip, limit)
        count = await self.post_repo.count_published()
        return posts, count
    
    async def add_comment(
        self,
        post_id: ObjectId,
        author_name: str,
        author_email: str,
        content: str
    ) -> Post:
        """Use case: Add comment to published post"""
        
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")
        
        # Create comment
        comment = Comment(
            author_name=author_name,
            author_email=author_email,
            content=content,
            status=CommentStatus.PENDING
        )
        
        # Enforce business rule
        post.add_comment(comment)
        
        # Persist changes
        saved_post = await self.post_repo.save(post)
        return saved_post
```

---

## 4. Implementation Guide

### 4.1 MongoDB Connection & Models

```python
# src/infrastructure/mongo/database.py

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from ...config.settings import settings

class MongoDatabase:
    """MongoDB connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_to_mongo(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.db = cls.client[settings.MONGODB_DB_NAME]
        
        # Create indexes
        await cls._create_indexes()
    
    @classmethod
    async def close_mongo_connection(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
    
    @classmethod
    async def _create_indexes(cls):
        """Create database indexes"""
        posts_collection = cls.db["posts"]
        
        # Create indexes
        await posts_collection.create_index("slug", unique=True)
        await posts_collection.create_index("status")
        await posts_collection.create_index("published_at")
        await posts_collection.create_index("tags")
        await posts_collection.create_index("author_id")
        
        # Other collections
        await cls.db["tags"].create_index("slug", unique=True)
        await cls.db["authors"].create_index("email", unique=True)
        await cls.db["authors"].create_index("username", unique=True)

def get_database() -> AsyncIOMotorDatabase:
    """Dependency: Get MongoDB database"""
    return MongoDatabase.db
```

### 4.2 Pydantic Models for MongoDB

```python
# src/infrastructure/mongo/models.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            return ObjectId(v)
        raise TypeError(f"ObjectId required")

class CommentModel(BaseModel):
    """Pydantic model for comment embedded in post"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    author_name: str
    author_email: str
    content: str
    status: str = "pending"
    likes: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class PostModel(BaseModel):
    """Pydantic model for Post in MongoDB"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author_id: Optional[PyObjectId] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    status: str = "draft"
    tags: List[str] = []
    category: Optional[str] = None
    views_count: int = 0
    likes_count: int = 0
    comments: List[CommentModel] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class AuthorModel(BaseModel):
    """Pydantic model for Author in MongoDB"""
    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    email: str
    username: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
```

### 4.3 Repository Implementation

```python
# src/infrastructure/mongo/repositories.py

from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...domain.blog.entities import Post, Author, Comment
from ...domain.blog.repositories import PostRepository, AuthorRepository
from ...domain.blog.value_objects import Slug, Email, PostStatus, CommentStatus
from .models import PostModel, AuthorModel, CommentModel

class MongoPostRepository(PostRepository):
    """MongoDB implementation of PostRepository"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["posts"]
    
    async def save(self, post: Post) -> Post:
        """Save post to MongoDB"""
        post_data = {
            "_id": post.id,
            "slug": str(post.slug),
            "title": post.title,
            "content": post.content,
            "excerpt": post.excerpt,
            "author_id": post.author_id,
            "author_name": post.author_name,
            "author_email": post.author_email,
            "status": post.status.value,
            "tags": post.tags,
            "category": post.category,
            "views_count": post.views_count,
            "likes_count": post.likes_count,
            "comments": [
                {
                    "_id": c.id,
                    "author_name": c.author_name,
                    "author_email": c.author_email,
                    "content": c.content,
                    "status": c.status.value,
                    "likes": c.likes,
                    "created_at": c.created_at
                }
                for c in post.comments
            ],
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at
        }
        
        await self.collection.update_one(
            {"_id": post.id},
            {"$set": post_data},
            upsert=True
        )
        return post
    
    async def get_by_id(self, post_id: ObjectId) -> Optional[Post]:
        """Get post by ID"""
        result = await self.collection.find_one({"_id": post_id})
        if not result:
            return None
        return self._to_post_entity(result)
    
    async def get_by_slug(self, slug: Slug) -> Optional[Post]:
        """Get post by slug"""
        result = await self.collection.find_one({"slug": str(slug)})
        if not result:
            return None
        return self._to_post_entity(result)
    
    async def find_published(self, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find published posts"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return [self._to_post_entity(doc) for doc in results]
    
    async def find_by_tag(self, tag: str, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find posts by tag"""
        cursor = self.collection.find(
            {"status": PostStatus.PUBLISHED.value, "tags": tag}
        ).sort("published_at", -1).skip(skip).limit(limit)
        
        results = await cursor.to_list(length=None)
        return [self._to_post_entity(doc) for doc in results]
    
    async def delete(self, post_id: ObjectId) -> bool:
        """Delete post"""
        result = await self.collection.delete_one({"_id": post_id})
        return result.deleted_count > 0
    
    async def count_published(self) -> int:
        """Count published posts"""
        return await self.collection.count_documents(
            {"status": PostStatus.PUBLISHED.value}
        )
    
    def _to_post_entity(self, doc: dict) -> Post:
        """Convert MongoDB document to Post entity"""
        comments = [
            Comment(
                id=c["_id"],
                author_name=c["author_name"],
                author_email=c["author_email"],
                content=c["content"],
                status=CommentStatus(c["status"]),
                likes=c.get("likes", 0),
                created_at=c["created_at"]
            )
            for c in doc.get("comments", [])
        ]
        
        return Post(
            id=doc["_id"],
            slug=Slug(doc["slug"]),
            title=doc["title"],
            content=doc["content"],
            excerpt=doc.get("excerpt"),
            author_id=doc.get("author_id"),
            author_name=doc.get("author_name"),
            author_email=doc.get("author_email"),
            status=PostStatus(doc["status"]),
            tags=doc.get("tags", []),
            category=doc.get("category"),
            views_count=doc.get("views_count", 0),
            likes_count=doc.get("likes_count", 0),
            comments=comments,
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            published_at=doc.get("published_at")
        )
```

### 4.4 FastAPI Routes

```python
# src/presentation/routers/blog.py

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...application.blog.services import PostApplicationService
from ...infrastructure.mongo.repositories import MongoPostRepository
from ...infrastructure.mongo.database import get_database
from ...presentation.schemas import (
    PostResponse,
    PostCreateRequest,
    CommentCreateRequest
)

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

async def get_post_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PostApplicationService:
    """Dependency: Get post application service"""
    post_repo = MongoPostRepository(db)
    return PostApplicationService(post_repo)

@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blog post"
)
async def create_post(
    request: PostCreateRequest,
    service: PostApplicationService = Depends(get_post_service)
):
    """Create a new blog post"""
    try:
        post = await service.create_post(
            title=request.title,
            content=request.content,
            slug_str=request.slug,
            author_id=ObjectId(request.author_id),
            excerpt=request.excerpt,
            tags=request.tags,
            category=request.category
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "",
    response_model=dict,
    summary="Get published posts with pagination"
)
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: PostApplicationService = Depends(get_post_service)
):
    """Retrieve published blog posts"""
    posts, total = await service.get_published_posts(skip, limit)
    return {
        "items": posts,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{post_id}", response_model=PostResponse, summary="Get post by ID")
async def get_post(
    post_id: str,
    service: PostApplicationService = Depends(get_post_service)
):
    """Get a specific post by ID"""
    try:
        post = await service.post_repo.get_by_id(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post.record_view()  # Record view
        await service.post_repo.save(post)
        return post
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/publish", response_model=PostResponse, summary="Publish a post")
async def publish_post(
    post_id: str,
    service: PostApplicationService = Depends(get_post_service)
):
    """Publish a draft post"""
    try:
        post = await service.publish_post(ObjectId(post_id))
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/comments", response_model=PostResponse, summary="Add comment to post")
async def add_comment(
    post_id: str,
    request: CommentCreateRequest,
    service: PostApplicationService = Depends(get_post_service)
):
    """Add a comment to a published post"""
    try:
        post = await service.add_comment(
            post_id=ObjectId(post_id),
            author_name=request.author_name,
            author_email=request.author_email,
            content=request.content
        )
        return post
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 4.5 Request/Response Schemas

```python
# src/presentation/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CommentResponse(BaseModel):
    id: str = Field(alias="_id")
    author_name: str
    author_email: str
    content: str
    status: str
    likes: int
    created_at: datetime
    
    class Config:
        populate_by_name = True

class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    slug: str = Field(..., regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    author_id: str
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None

class PostResponse(BaseModel):
    id: str = Field(alias="_id")
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    status: str
    tags: List[str]
    category: Optional[str] = None
    views_count: int
    likes_count: int
    comments: List[CommentResponse] = []
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True

class CommentCreateRequest(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=100)
    author_email: str
    content: str = Field(..., min_length=1, max_length=2000)
```

---

## 5. Docker Compose Setup

### 5.1 docker-compose.yml

```yaml
version: '3.9'

services:
  mongodb:
    image: mongo:7.0
    container_name: personal-blog-mongo
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USERNAME:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD:-password}
      MONGO_INITDB_DATABASE: ${MONGODB_DB_NAME:-blog}
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
    networks:
      - blog-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test -u ${MONGO_ROOT_USERNAME:-admin} -p ${MONGO_ROOT_PASSWORD:-password}
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: personal-blog-backend
    environment:
      MONGODB_URL: mongodb://${MONGO_ROOT_USERNAME:-admin}:${MONGO_ROOT_PASSWORD:-password}@mongodb:27017/?authSource=admin
      MONGODB_DB_NAME: ${MONGODB_DB_NAME:-blog}
      LOG_LEVEL: ${LOG_LEVEL:-info}
    ports:
      - "8000:8000"
    depends_on:
      mongodb:
        condition: service_healthy
    volumes:
      - ./src:/app/src
    networks:
      - blog-network
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  mongodb_data:
  mongodb_config:

networks:
  blog-network:
    driver: bridge
```

### 5.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.3 .env.example

```env
# MongoDB Configuration
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=secure_password_here
MONGODB_DB_NAME=blog

# FastAPI Configuration
LOG_LEVEL=info
DEBUG=false

# API Configuration
API_V1_PREFIX=/api/v1
```

### 5.4 requirements.txt

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pymongo==4.6.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

---

## 6. Main Application Entry Point

```python
# src/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.settings import settings
from .infrastructure.mongo.database import MongoDatabase
from .presentation.routers import blog

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    await MongoDatabase.connect_to_mongo()
    yield
    # Shutdown
    await MongoDatabase.close_mongo_connection()

app = FastAPI(
    title="Personal Blog API",
    description="A clean DDD-based blog API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(blog.router)

@app.get("/", tags=["health"])
async def root():
    return {"message": "Personal Blog API - DDD Architecture"}

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
```

### 6.1 Configuration

```python
# src/config/settings.py

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    MONGODB_URL: str = "mongodb://admin:password@localhost:27017/?authSource=admin"
    MONGODB_DB_NAME: str = "blog"
    LOG_LEVEL: str = "info"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 7. Running the Application

### 7.1 Setup

```bash
# Clone and navigate to project
cd personal-blog

# Create .env file
cp .env.example .env

# Build and start containers
docker-compose up --build

# Verify services
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 7.2 Testing API Endpoints

```bash
# Get published posts
curl http://localhost:8000/api/v1/posts

# Create a post (need author_id first)
curl -X POST http://localhost:8000/api/v1/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is the content",
    "slug": "my-first-post",
    "author_id": "507f1f77bcf86cd799439011"
  }'
```

---

## 8. Key DDD Principles Applied

**Bounded Context:** Blog domain is isolated with clear boundaries
**Ubiquitous Language:** Domain language (Post, Comment, Author) used consistently
**Aggregates:** Post is the aggregate root containing Comments
**Value Objects:** Email, Slug enforce invariants and validation
**Repository Pattern:** Data access abstraction through interfaces
**Application Services:** Orchestrate use cases maintaining domain integrity
**Separation of Concerns:** Clear layering (Domain → Application → Infrastructure → Presentation)

---

## 9. Next Steps for Enhancement

1. Add authentication/authorization layer
2. Implement domain events for post published notifications
3. Add caching with Redis
4. Implement search functionality with Elasticsearch
5. Add comprehensive logging and monitoring
6. Write unit and integration tests
7. Add API documentation with OpenAPI
8. Implement pagination for comments
9. Add category and tag management endpoints
10. Implement soft deletes for audit trail

---

This guide provides a solid foundation for building a production-ready blog backend following DDD principles, with clean separation of concerns and maintainable code structure.
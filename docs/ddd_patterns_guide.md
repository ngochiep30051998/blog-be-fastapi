# Personal Blog - DDD Implementation: Best Practices & Patterns

Supplementary guide covering advanced patterns, testing strategies, and production-ready considerations.

---

## Table of Contents

1. Advanced DDD Patterns
2. Error Handling & Exceptions
3. Database Migrations
4. Testing Strategy
5. Performance Optimization
6. Security Considerations
7. Monitoring & Logging
8. Common Pitfalls & Solutions

---

## 1. Advanced DDD Patterns

### 1.1 Domain Events (Optional Enhancement)

Domain events represent things that happened in the domain that other parts need to be aware of:

```python
# src/domain/core/events.py

from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class DomainEvent:
    """Base class for all domain events"""
    occurred_at: datetime
    aggregate_id: Any

@dataclass
class PostPublishedEvent(DomainEvent):
    """Event fired when a post is published"""
    post_id: Any
    post_title: str
    author_id: Any

@dataclass
class CommentAddedEvent(DomainEvent):
    """Event fired when a comment is added to post"""
    post_id: Any
    comment_id: Any
    commenter_name: str

# In entities.py
class Post:
    def __init__(self, ...):
        self._events: List[DomainEvent] = []
    
    def publish(self):
        if self.status == PostStatus.PUBLISHED:
            raise ValueError("Post is already published")
        
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        
        # Record domain event
        self._events.append(
            PostPublishedEvent(
                occurred_at=datetime.utcnow(),
                aggregate_id=self.id,
                post_id=self.id,
                post_title=self.title,
                author_id=self.author_id
            )
        )
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get events that haven't been persisted"""
        return self._events.copy()
    
    def clear_events(self):
        """Clear events after persistence"""
        self._events.clear()
```

### 1.2 Specification Pattern for Complex Queries

```python
# src/domain/blog/specifications.py

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

class PostSpecification(ABC):
    """Base specification for post queries"""
    
    @abstractmethod
    def get_query_filter(self) -> dict:
        """Return MongoDB filter dict"""
        pass

class PublishedPostsSpecification(PostSpecification):
    """Specification: Published posts only"""
    
    def get_query_filter(self) -> dict:
        return {"status": "published"}

class RecentPostsSpecification(PostSpecification):
    """Specification: Posts from last N days"""
    
    def __init__(self, days: int = 7):
        self.days = days
    
    def get_query_filter(self) -> dict:
        cutoff_date = datetime.utcnow() - timedelta(days=self.days)
        return {
            "status": "published",
            "published_at": {"$gte": cutoff_date}
        }

class PostsByAuthorSpecification(PostSpecification):
    """Specification: Posts by specific author"""
    
    def __init__(self, author_id):
        self.author_id = author_id
    
    def get_query_filter(self) -> dict:
        return {"author_id": self.author_id}

class CompositeSpecification(PostSpecification):
    """Combine multiple specifications with AND logic"""
    
    def __init__(self, *specs: PostSpecification):
        self.specs = specs
    
    def get_query_filter(self) -> dict:
        filters = [spec.get_query_filter() for spec in self.specs]
        if len(filters) == 1:
            return filters[0]
        return {"$and": filters}

# Usage in repository
class MongoPostRepository(PostRepository):
    async def find_by_specification(self, spec: PostSpecification) -> List[Post]:
        """Find posts matching specification"""
        filter_dict = spec.get_query_filter()
        cursor = self.collection.find(filter_dict)
        results = await cursor.to_list(length=None)
        return [self._to_post_entity(doc) for doc in results]

# In service
class PostApplicationService:
    async def get_recent_published_posts(self, days: int = 7):
        """Get recently published posts"""
        spec = CompositeSpecification(
            PublishedPostsSpecification(),
            RecentPostsSpecification(days)
        )
        return await self.post_repo.find_by_specification(spec)
```

### 1.3 Unit of Work Pattern (Optional)

```python
# src/domain/core/unit_of_work.py

from abc import ABC, abstractmethod
from typing import Optional

class UnitOfWork(ABC):
    """Unit of work pattern for transaction management"""
    
    def __init__(self, db):
        self.db = db
        self.session = None
    
    @abstractmethod
    async def begin(self):
        """Start transaction"""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit transaction"""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback transaction"""
        pass
    
    async def __aenter__(self):
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

# Usage in service
class PostApplicationService:
    async def publish_and_notify(self, post_id: ObjectId, unit_of_work: UnitOfWork):
        """Atomic operation: publish post and send notification"""
        async with unit_of_work:
            post = await self.post_repo.get_by_id(post_id)
            post.publish()
            await self.post_repo.save(post)
            # If any error occurs, rollback all changes
```

---

## 2. Error Handling & Exceptions

### 2.1 Domain Exceptions

```python
# src/domain/core/exceptions.py

class DomainException(Exception):
    """Base exception for domain layer"""
    pass

# src/domain/blog/exceptions.py

class PostException(DomainException):
    """Base exception for post domain"""
    pass

class PostNotFoundError(PostException):
    """Post not found"""
    def __init__(self, post_id):
        self.post_id = post_id
        super().__init__(f"Post {post_id} not found")

class InvalidPostStatusError(PostException):
    """Invalid post status transition"""
    def __init__(self, current_status, target_status):
        self.current = current_status
        self.target = target_status
        super().__init__(
            f"Cannot transition from {current_status} to {target_status}"
        )

class PostAlreadyPublishedError(PostException):
    """Attempting to publish already published post"""
    def __init__(self, post_id):
        super().__init__(f"Post {post_id} is already published")

class InvalidSlugError(PostException):
    """Invalid slug format"""
    def __init__(self, slug):
        self.slug = slug
        super().__init__(f"Invalid slug format: {slug}")

class UnauthorizedCommentError(PostException):
    """Cannot add comment to unpublished post"""
    def __init__(self, post_id):
        super().__init__(
            f"Cannot add comments to unpublished post {post_id}"
        )

# src/core/exceptions.py (Application/Infrastructure)

class ApplicationException(Exception):
    """Base application exception"""
    pass

class RepositoryException(ApplicationException):
    """Database operation error"""
    pass

class ValidationException(ApplicationException):
    """Input validation error"""
    pass
```

### 2.2 Exception Handlers

```python
# src/presentation/exception_handlers.py

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from ...core.exceptions import ApplicationException, ValidationException
from ...domain.core.exceptions import DomainException
from ...domain.blog.exceptions import PostNotFoundError

def setup_exception_handlers(app: FastAPI):
    """Register exception handlers"""
    
    @app.exception_handler(PostNotFoundError)
    async def post_not_found_handler(request: Request, exc: PostNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "POST_NOT_FOUND",
                "message": str(exc),
                "details": {"post_id": str(exc.post_id)}
            }
        )
    
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "DOMAIN_ERROR",
                "message": str(exc)
            }
        )
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": str(exc)
            }
        )
    
    @app.exception_handler(ApplicationException)
    async def application_exception_handler(request: Request, exc: ApplicationException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "APPLICATION_ERROR",
                "message": "An unexpected error occurred"
            }
        )
```

---

## 3. Database Migrations

### 3.1 Alembic-style Migration (Manual for MongoDB)

```python
# src/infrastructure/mongo/migrations.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

class Migration:
    """Base migration class"""
    
    version: str
    description: str
    
    async def up(self, db: AsyncIOMotorDatabase):
        """Apply migration"""
        raise NotImplementedError
    
    async def down(self, db: AsyncIOMotorDatabase):
        """Rollback migration"""
        raise NotImplementedError

class AddCommentStatusFieldMigration(Migration):
    """Migration: Add comment status field"""
    version = "20240101_001"
    description = "Add status field to comments"
    
    async def up(self, db: AsyncIOMotorDatabase):
        """Add default status to all comments"""
        posts = db["posts"]
        await posts.update_many(
            {"comments": {"$exists": True}},
            [
                {
                    "$set": {
                        "comments": {
                            "$map": {
                                "input": "$comments",
                                "as": "comment",
                                "in": {
                                    "$mergeObjects": [
                                        "$$comment",
                                        {"status": "approved"}
                                    ]
                                }
                            }
                        }
                    }
                }
            ]
        )
    
    async def down(self, db: AsyncIOMotorDatabase):
        """Remove status field from comments"""
        posts = db["posts"]
        await posts.update_many(
            {"comments": {"$exists": True}},
            [
                {
                    "$set": {
                        "comments": {
                            "$map": {
                                "input": "$comments",
                                "as": "comment",
                                "in": {
                                    "$unsetField": {
                                        "field": "status",
                                        "input": "$$comment"
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        )

# Migration runner
class MigrationRunner:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.migrations_collection = db["migrations"]
    
    async def run_migrations(self, migrations: list):
        """Run pending migrations"""
        for migration in migrations:
            applied = await self.migrations_collection.find_one(
                {"version": migration.version}
            )
            
            if not applied:
                print(f"Running migration: {migration.description}")
                await migration.up(self.db)
                await self.migrations_collection.insert_one({
                    "version": migration.version,
                    "description": migration.description,
                    "applied_at": datetime.utcnow()
                })
                print(f"Migration completed: {migration.version}")
```

---

## 4. Testing Strategy

### 4.1 Unit Tests for Domain

```python
# tests/unit/domain/blog/test_post_entity.py

import pytest
from bson import ObjectId
from datetime import datetime
from src.domain.blog.entities import Post, Comment
from src.domain.blog.value_objects import Slug, PostStatus, CommentStatus
from src.domain.blog.exceptions import PostAlreadyPublishedError

@pytest.fixture
def sample_post():
    """Create sample post for testing"""
    return Post(
        id=ObjectId(),
        slug=Slug("test-post"),
        title="Test Post",
        content="Test content",
        status=PostStatus.DRAFT
    )

def test_post_publish(sample_post):
    """Test publishing a post"""
    assert sample_post.status == PostStatus.DRAFT
    assert sample_post.published_at is None
    
    sample_post.publish()
    
    assert sample_post.status == PostStatus.PUBLISHED
    assert sample_post.published_at is not None

def test_post_cannot_publish_twice(sample_post):
    """Test that published post cannot be published again"""
    sample_post.publish()
    
    with pytest.raises(ValueError):
        sample_post.publish()

def test_add_comment_to_draft_post_fails(sample_post):
    """Test that comments cannot be added to draft posts"""
    comment = Comment(
        author_name="John",
        author_email="john@example.com",
        content="Nice post!"
    )
    
    with pytest.raises(ValueError):
        sample_post.add_comment(comment)

def test_add_comment_to_published_post(sample_post):
    """Test adding comment to published post"""
    sample_post.publish()
    
    comment = Comment(
        author_name="John",
        author_email="john@example.com",
        content="Nice post!"
    )
    
    sample_post.add_comment(comment)
    
    assert len(sample_post.comments) == 1
    assert sample_post.comments[0].author_name == "John"

def test_record_view(sample_post):
    """Test recording post views"""
    assert sample_post.views_count == 0
    
    sample_post.record_view()
    sample_post.record_view()
    
    assert sample_post.views_count == 2

def test_like_post(sample_post):
    """Test liking a post"""
    assert sample_post.likes_count == 0
    
    sample_post.like()
    
    assert sample_post.likes_count == 1
```

### 4.2 Repository Tests

```python
# tests/integration/infrastructure/mongo/test_post_repository.py

import pytest
from bson import ObjectId
from src.infrastructure.mongo.repositories import MongoPostRepository
from src.domain.blog.entities import Post
from src.domain.blog.value_objects import Slug, PostStatus

@pytest.fixture
async def post_repository(test_db):
    """Create repository with test database"""
    return MongoPostRepository(test_db)

@pytest.mark.asyncio
async def test_save_new_post(post_repository, sample_post):
    """Test saving a new post"""
    saved_post = await post_repository.save(sample_post)
    
    assert saved_post.id == sample_post.id
    
    # Verify it was persisted
    retrieved = await post_repository.get_by_id(sample_post.id)
    assert retrieved is not None
    assert retrieved.title == sample_post.title

@pytest.mark.asyncio
async def test_get_by_slug(post_repository, sample_post):
    """Test retrieving post by slug"""
    await post_repository.save(sample_post)
    
    retrieved = await post_repository.get_by_slug(sample_post.slug)
    
    assert retrieved is not None
    assert retrieved.slug == sample_post.slug

@pytest.mark.asyncio
async def test_find_published_posts(post_repository):
    """Test finding published posts"""
    # Create and save posts
    post1 = Post(
        id=ObjectId(),
        slug=Slug("post-1"),
        title="Post 1",
        content="Content 1",
        status=PostStatus.PUBLISHED
    )
    post1.published_at = datetime.utcnow()
    
    post2 = Post(
        id=ObjectId(),
        slug=Slug("post-2"),
        title="Post 2",
        content="Content 2",
        status=PostStatus.DRAFT
    )
    
    await post_repository.save(post1)
    await post_repository.save(post2)
    
    # Find published
    published = await post_repository.find_published()
    
    assert len(published) == 1
    assert published[0].status == PostStatus.PUBLISHED
```

---

## 5. Performance Optimization

### 5.1 Database Indexing Strategy

```python
# src/infrastructure/mongo/database.py

class MongoDatabase:
    @classmethod
    async def _create_indexes(cls):
        """Create production-optimized indexes"""
        posts = cls.db["posts"]
        
        # Single field indexes
        await posts.create_index("slug", unique=True)
        await posts.create_index("status", sparse=True)
        await posts.create_index("published_at", sparse=True)
        await posts.create_index("author_id", sparse=True)
        await posts.create_index("created_at")
        
        # Text index for full-text search
        await posts.create_index([("title", "text"), ("content", "text")])
        
        # Compound index for common queries
        await posts.create_index([("status", 1), ("published_at", -1)])
        
        # For tag queries
        await posts.create_index("tags")
        
        # TTL index for soft deletes (optional)
        # await posts.create_index(
        #     "deleted_at",
        #     expireAfterSeconds=2592000  # 30 days
        # )
```

### 5.2 Query Optimization

```python
# src/application/blog/services.py

class PostApplicationService:
    # Instead of fetching full post with all comments
    async def get_post_summary(self, post_id: ObjectId) -> dict:
        """Optimized query: get post without loading all comments"""
        return await self.db["posts"].find_one(
            {"_id": post_id},
            {
                "title": 1,
                "slug": 1,
                "excerpt": 1,
                "author_name": 1,
                "published_at": 1,
                "comments": {  # Project only comment count, not full objects
                    "$size": "$comments"
                }
            }
        )
    
    # Pagination for comments
    async def get_post_comments(
        self,
        post_id: ObjectId,
        skip: int = 0,
        limit: int = 10
    ) -> dict:
        """Get paginated comments for a post"""
        pipeline = [
            {"$match": {"_id": post_id}},
            {
                "$project": {
                    "comments": {
                        "$slice": ["$comments", skip, limit]
                    },
                    "total_comments": {"$size": "$comments"}
                }
            }
        ]
        
        result = await self.db["posts"].aggregate(pipeline).to_list(1)
        return result[0] if result else None
```

### 5.3 Caching Strategy (Optional)

```python
# src/infrastructure/cache.py (if Redis added)

import redis.asyncio as redis
from functools import wraps
import json

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = None
        self.redis_url = redis_url
    
    async def connect(self):
        self.redis = await redis.from_url(self.redis_url)
    
    async def disconnect(self):
        await self.redis.close()
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in kwargs.items()])
        return ":".join(key_parts)
    
    def cache_result(self, ttl: int = 3600):
        """Decorator to cache async function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = self.cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached = await self.redis.get(key)
                if cached:
                    return json.loads(cached)
                
                # Call function
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.redis.setex(
                    key,
                    ttl,
                    json.dumps(result, default=str)
                )
                
                return result
            return wrapper
        return decorator

# Usage
cache = CacheManager("redis://localhost")

class PostApplicationService:
    @cache.cache_result(ttl=3600)
    async def get_published_posts(self, skip: int = 0, limit: int = 10):
        """This result will be cached for 1 hour"""
        return await self.post_repo.find_published(skip, limit)
```

---

## 6. Security Considerations

### 6.1 Input Validation

```python
# src/core/validators.py

import re
from pydantic import validator, field_validator

class SecurePostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10, max_length=50000)
    slug: str = Field(..., regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    
    @field_validator('content')
    @classmethod
    def content_no_html(cls, v):
        """Prevent HTML injection"""
        if '<' in v or '>' in v:
            raise ValueError('HTML tags not allowed')
        return v
    
    @field_validator('title')
    @classmethod
    def title_no_sql(cls, v):
        """Basic SQL injection prevention"""
        dangerous_patterns = [';', 'DROP', 'DELETE', 'INSERT']
        if any(pattern in v.upper() for pattern in dangerous_patterns):
            raise ValueError('Invalid characters in title')
        return v
```

### 6.2 Output Sanitization

```python
# src/utils/sanitizer.py

from bleach import clean

class ContentSanitizer:
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    
    @staticmethod
    def sanitize(html_content: str) -> str:
        """Remove potentially dangerous HTML"""
        return clean(
            html_content,
            tags=ContentSanitizer.ALLOWED_TAGS,
            attributes=ContentSanitizer.ALLOWED_ATTRIBUTES,
            strip=True
        )

# Usage in repository before saving
class MongoPostRepository:
    async def save(self, post: Post) -> Post:
        post_data = {
            "content": ContentSanitizer.sanitize(post.content),
            ...
        }
        # Save sanitized content
```

---

## 7. Monitoring & Logging

### 7.1 Structured Logging

```python
# src/infrastructure/logging.py

import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_event(self, event: str, **kwargs):
        """Log structured event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))
    
    def log_error(self, error: str, exception: Exception = None, **kwargs):
        """Log structured error"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "exception": str(exception) if exception else None,
            **kwargs
        }
        self.logger.error(json.dumps(log_entry))

# Usage in services
logger = StructuredLogger(__name__)

class PostApplicationService:
    async def create_post(self, ...):
        try:
            logger.log_event("post_creation_started", author_id=str(author_id))
            post = await self.post_repo.save(post)
            logger.log_event("post_created", post_id=str(post.id), author_id=str(author_id))
            return post
        except Exception as e:
            logger.log_error("post_creation_failed", e, author_id=str(author_id))
            raise
```

---

## 8. Common Pitfalls & Solutions

### Pitfall 1: Mixing Domain and Infrastructure Logic

❌ **Wrong:**
```python
# In domain entity
class Post:
    async def save_to_db(self):
        """This violates DDD - domain shouldn't know about DB"""
        await db.posts.insert_one(self.__dict__)
```

✅ **Right:**
```python
# In repository (infrastructure layer)
class MongoPostRepository:
    async def save(self, post: Post):
        """Repository handles persistence"""
        # Convert entity to MongoDB format
        # Save to database
        pass
```

### Pitfall 2: Circular Dependencies

❌ **Wrong:**
```python
# Service imports Repository which imports Service
from services import PostService

class PostRepository:
    def __init__(self, service: PostService):
        self.service = service
```

✅ **Right:**
```python
# Unidirectional dependency
class PostApplicationService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo
```

### Pitfall 3: Ignoring Business Rules in Infrastructure

❌ **Wrong:**
```python
# Repository bypasses domain logic
class MongoPostRepository:
    async def publish_post(self, post_id: ObjectId):
        await self.collection.update_one(
            {"_id": post_id},
            {"$set": {"status": "published"}}
        )
        # No validation of business rules!
```

✅ **Right:**
```python
# Service enforces domain rules
class PostApplicationService:
    async def publish_post(self, post_id: ObjectId):
        post = await self.post_repo.get_by_id(post_id)
        post.publish()  # This enforces business rule
        await self.post_repo.save(post)
```

### Pitfall 4: Over-fetching Data

❌ **Wrong:**
```python
# Load entire post with all comments when you only need the title
post = await self.post_repo.get_by_id(post_id)  # Loads everything
return {"title": post.title}
```

✅ **Right:**
```python
# Load only what you need
result = await self.db["posts"].find_one(
    {"_id": post_id},
    {"title": 1, "_id": 0}
)
return result
```

---

## Next Steps

1. Implement authentication/authorization
2. Add API rate limiting
3. Implement soft deletes with audit trails
4. Add comprehensive test coverage (>80%)
5. Set up CI/CD pipeline
6. Implement API versioning
7. Add OpenAPI documentation
8. Deploy to production environment
9. Set up monitoring and alerting
10. Document API for external consumers

---

This guide provides production-ready patterns and best practices for building enterprise-grade blog applications with FastAPI and MongoDB using Domain-Driven Design principles.
# Personal Blog - Multi-File Structure Organization

Complete guide for splitting monolithic files into modular, well-organized Python packages.

---

## Table of Contents

1. Domain Layer - Multi-File Structure
2. Application Layer - Multi-File Structure
3. Infrastructure Layer - Multi-File Structure
4. Presentation Layer - Multi-File Structure
5. Import Organization
6. Benefits & Best Practices

---

## 1. Domain Layer - Multi-File Structure

### 1.1 Complete Domain Directory Structure

```
src/domain/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── exceptions.py          # Base exceptions
│   ├── events.py              # Domain events (optional)
│   └── value_object.py        # Base value object class
│
└── blog/
    ├── __init__.py
    ├── entities/
    │   ├── __init__.py
    │   ├── post.py            # Post aggregate root
    │   ├── author.py          # Author entity
    │   └── comment.py         # Comment value object
    │
    ├── value_objects/
    │   ├── __init__.py
    │   ├── email.py           # Email value object
    │   ├── slug.py            # Slug value object
    │   ├── statuses.py        # PostStatus, CommentStatus enums
    │   └── composite.py       # Complex value objects
    │
    ├── repositories/
    │   ├── __init__.py
    │   ├── post_repository.py  # PostRepository interface
    │   ├── author_repository.py # AuthorRepository interface
    │   └── tag_repository.py   # TagRepository interface
    │
    └── exceptions/
        ├── __init__.py
        ├── post_exceptions.py  # Post-related exceptions
        ├── comment_exceptions.py # Comment exceptions
        ├── author_exceptions.py # Author exceptions
        └── validation_exceptions.py # Validation errors
```

### 1.2 Domain - Core Files

```python
# src/domain/core/__init__.py

from .exceptions import DomainException
from .value_object import ValueObject
from .events import DomainEvent

__all__ = [
    "DomainException",
    "ValueObject",
    "DomainEvent",
]
```

```python
# src/domain/core/exceptions.py

class DomainException(Exception):
    """Base exception for domain layer"""
    pass
```

```python
# src/domain/core/value_object.py

from abc import ABC
from dataclasses import dataclass

@dataclass(frozen=True)
class ValueObject(ABC):
    """Base class for all value objects"""
    pass
```

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
```

### 1.3 Domain - Value Objects

```python
# src/domain/blog/value_objects/__init__.py

from .email import Email
from .slug import Slug
from .statuses import PostStatus, CommentStatus

__all__ = [
    "Email",
    "Slug",
    "PostStatus",
    "CommentStatus",
]
```

```python
# src/domain/blog/value_objects/email.py

import re
from dataclasses import dataclass
from ..exceptions import ValidationExceptions

@dataclass(frozen=True)
class Email:
    """Email value object with validation"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValidationExceptions.InvalidEmailError(self.value)
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other):
        if isinstance(other, Email):
            return self.value == other.value
        return self.value == str(other)
    
    def __hash__(self):
        return hash(self.value)
```

```python
# src/domain/blog/value_objects/slug.py

import re
from dataclasses import dataclass
from ..exceptions import ValidationExceptions

@dataclass(frozen=True)
class Slug:
    """URL-friendly slug value object"""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_slug(self.value):
            raise ValidationExceptions.InvalidSlugError(self.value)
    
    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return re.match(pattern, slug) is not None
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other):
        if isinstance(other, Slug):
            return self.value == other.value
        return self.value == str(other)
    
    def __hash__(self):
        return hash(self.value)
```

```python
# src/domain/blog/value_objects/statuses.py

from enum import Enum

class PostStatus(str, Enum):
    """Post status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class CommentStatus(str, Enum):
    """Comment status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SPAM = "spam"
```

### 1.4 Domain - Entities

```python
# src/domain/blog/entities/__init__.py

from .author import Author
from .comment import Comment
from .post import Post

__all__ = [
    "Author",
    "Comment",
    "Post",
]
```

```python
# src/domain/blog/entities/author.py

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from ..value_objects import Email

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
    
    def update_profile(self, name: str, bio: Optional[str] = None, avatar_url: Optional[str] = None):
        """Update author profile"""
        self.name = name
        if bio:
            self.bio = bio
        if avatar_url:
            self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()
```

```python
# src/domain/blog/entities/comment.py

from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from ..value_objects import CommentStatus

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
    
    def reject(self):
        """Business rule: reject comment"""
        if self.status != CommentStatus.PENDING:
            raise ValueError("Only pending comments can be rejected")
        self.status = CommentStatus.REJECTED
    
    def mark_as_spam(self):
        """Business rule: mark as spam"""
        self.status = CommentStatus.SPAM
    
    def add_like(self):
        """Business rule: increment likes"""
        self.likes += 1
    
    def remove_like(self):
        """Business rule: decrement likes"""
        if self.likes > 0:
            self.likes -= 1
```

```python
# src/domain/blog/entities/post.py

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..value_objects import Slug, PostStatus
from .comment import Comment
from ..exceptions import PostExceptions

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
            raise PostExceptions.PostAlreadyPublishedError(self.id)
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def archive(self):
        """Business rule: Archive a published post"""
        if self.status != PostStatus.PUBLISHED:
            raise PostExceptions.CannotArchiveUnpublishedPostError(self.id)
        self.status = PostStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def unarchive(self):
        """Business rule: Unarchive a post"""
        if self.status != PostStatus.ARCHIVED:
            raise PostExceptions.PostNotArchivedError(self.id)
        self.status = PostStatus.PUBLISHED
        self.updated_at = datetime.utcnow()
    
    def add_comment(self, comment: Comment) -> None:
        """Business rule: Add comment to post"""
        if self.status != PostStatus.PUBLISHED:
            raise PostExceptions.CannotCommentUnpublishedPostError(self.id)
        self.comments.append(comment)
        self.updated_at = datetime.utcnow()
    
    def remove_comment(self, comment_id: ObjectId) -> bool:
        """Business rule: Remove comment from post"""
        initial_length = len(self.comments)
        self.comments = [c for c in self.comments if c.id != comment_id]
        if len(self.comments) < initial_length:
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def record_view(self) -> None:
        """Business rule: Increment view count"""
        self.views_count += 1
        self.updated_at = datetime.utcnow()
    
    def like(self) -> None:
        """Business rule: Like post"""
        self.likes_count += 1
        self.updated_at = datetime.utcnow()
    
    def update_content(
        self,
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None
    ):
        """Business rule: Update post content"""
        self.title = title
        self.content = content
        if excerpt:
            self.excerpt = excerpt
        if tags:
            self.tags = tags
        if category:
            self.category = category
        self.updated_at = datetime.utcnow()
```

### 1.5 Domain - Repositories

```python
# src/domain/blog/repositories/__init__.py

from .post_repository import PostRepository
from .author_repository import AuthorRepository
from .tag_repository import TagRepository

__all__ = [
    "PostRepository",
    "AuthorRepository",
    "TagRepository",
]
```

```python
# src/domain/blog/repositories/post_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from bson import ObjectId
from ..entities import Post
from ..value_objects import Slug

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
    async def find_by_author(self, author_id: ObjectId, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find posts by author"""
        pass
    
    @abstractmethod
    async def delete(self, post_id: ObjectId) -> bool:
        """Delete post"""
        pass
    
    @abstractmethod
    async def count_published(self) -> int:
        """Count published posts"""
        pass
```

```python
# src/domain/blog/repositories/author_repository.py

from abc import ABC, abstractmethod
from typing import Optional
from bson import ObjectId
from ..entities import Author
from ..value_objects import Email

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
    async def get_by_email(self, email: Email) -> Optional[Author]:
        """Get author by email"""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[Author]:
        """Get author by username"""
        pass
    
    @abstractmethod
    async def delete(self, author_id: ObjectId) -> bool:
        """Delete author"""
        pass
```

```python
# src/domain/blog/repositories/tag_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from bson import ObjectId

class TagRepository(ABC):
    """Tag repository interface"""
    
    @abstractmethod
    async def get_popular_tags(self, limit: int = 20) -> List[dict]:
        """Get most used tags"""
        pass
    
    @abstractmethod
    async def count_posts_by_tag(self, tag: str) -> int:
        """Count posts with tag"""
        pass
```

### 1.6 Domain - Exceptions

```python
# src/domain/blog/exceptions/__init__.py

from .post_exceptions import PostExceptions
from .comment_exceptions import CommentExceptions
from .author_exceptions import AuthorExceptions
from .validation_exceptions import ValidationExceptions

__all__ = [
    "PostExceptions",
    "CommentExceptions",
    "AuthorExceptions",
    "ValidationExceptions",
]
```

```python
# src/domain/blog/exceptions/post_exceptions.py

from ...core.exceptions import DomainException

class PostException(DomainException):
    """Base exception for post domain"""
    pass

class PostExceptions:
    """Collection of post-related exceptions"""
    
    class PostNotFoundError(PostException):
        def __init__(self, post_id):
            self.post_id = post_id
            super().__init__(f"Post {post_id} not found")
    
    class PostAlreadyPublishedError(PostException):
        def __init__(self, post_id):
            super().__init__(f"Post {post_id} is already published")
    
    class CannotCommentUnpublishedPostError(PostException):
        def __init__(self, post_id):
            super().__init__(f"Cannot add comments to unpublished post {post_id}")
    
    class CannotArchiveUnpublishedPostError(PostException):
        def __init__(self, post_id):
            super().__init__(f"Cannot archive unpublished post {post_id}")
    
    class PostNotArchivedError(PostException):
        def __init__(self, post_id):
            super().__init__(f"Post {post_id} is not archived")
    
    class InvalidPostStatusError(PostException):
        def __init__(self, current, target):
            super().__init__(f"Cannot transition from {current} to {target}")
```

```python
# src/domain/blog/exceptions/comment_exceptions.py

from ...core.exceptions import DomainException

class CommentException(DomainException):
    """Base exception for comment domain"""
    pass

class CommentExceptions:
    """Collection of comment-related exceptions"""
    
    class CommentNotFoundError(CommentException):
        def __init__(self, comment_id):
            super().__init__(f"Comment {comment_id} not found")
    
    class InvalidCommentStatusError(CommentException):
        def __init__(self, current, target):
            super().__init__(f"Cannot transition comment from {current} to {target}")
```

```python
# src/domain/blog/exceptions/author_exceptions.py

from ...core.exceptions import DomainException

class AuthorException(DomainException):
    """Base exception for author domain"""
    pass

class AuthorExceptions:
    """Collection of author-related exceptions"""
    
    class AuthorNotFoundError(AuthorException):
        def __init__(self, author_id):
            super().__init__(f"Author {author_id} not found")
    
    class DuplicateEmailError(AuthorException):
        def __init__(self, email):
            super().__init__(f"Author with email {email} already exists")
    
    class DuplicateUsernameError(AuthorException):
        def __init__(self, username):
            super().__init__(f"Username {username} already exists")
```

```python
# src/domain/blog/exceptions/validation_exceptions.py

from ...core.exceptions import DomainException

class ValidationException(DomainException):
    """Base exception for validation errors"""
    pass

class ValidationExceptions:
    """Collection of validation exceptions"""
    
    class InvalidEmailError(ValidationException):
        def __init__(self, email):
            super().__init__(f"Invalid email format: {email}")
    
    class InvalidSlugError(ValidationException):
        def __init__(self, slug):
            super().__init__(f"Invalid slug format: {slug}")
    
    class InvalidTitleError(ValidationException):
        def __init__(self, reason):
            super().__init__(f"Invalid title: {reason}")
    
    class InvalidContentError(ValidationException):
        def __init__(self, reason):
            super().__init__(f"Invalid content: {reason}")
```

```python
# src/domain/blog/__init__.py

from .entities import Author, Comment, Post
from .value_objects import Email, Slug, PostStatus, CommentStatus
from .repositories import PostRepository, AuthorRepository, TagRepository
from .exceptions import PostExceptions, CommentExceptions, AuthorExceptions, ValidationExceptions

__all__ = [
    # Entities
    "Author",
    "Comment",
    "Post",
    # Value Objects
    "Email",
    "Slug",
    "PostStatus",
    "CommentStatus",
    # Repositories
    "PostRepository",
    "AuthorRepository",
    "TagRepository",
    # Exceptions
    "PostExceptions",
    "CommentExceptions",
    "AuthorExceptions",
    "ValidationExceptions",
]
```

---

## 2. Application Layer - Multi-File Structure

### 2.1 Complete Application Directory Structure

```
src/application/
├── __init__.py
├── blog/
│   ├── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── post_service.py       # PostApplicationService
│   │   ├── comment_service.py    # CommentApplicationService
│   │   └── author_service.py     # AuthorApplicationService
│   │
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── post_dto.py           # Post DTOs
│   │   ├── comment_dto.py        # Comment DTOs
│   │   └── author_dto.py         # Author DTOs
│   │
│   └── use_cases/
│       ├── __init__.py
│       ├── create_post.py        # Create post use case
│       ├── publish_post.py       # Publish post use case
│       ├── add_comment.py        # Add comment use case
│       └── get_posts.py          # Get posts use case
```

### 2.2 Application - DTOs

```python
# src/application/blog/dto/__init__.py

from .post_dto import (
    PostCreateDTO,
    PostUpdateDTO,
    PostResponseDTO,
)
from .comment_dto import (
    CommentCreateDTO,
    CommentResponseDTO,
)
from .author_dto import (
    AuthorCreateDTO,
    AuthorResponseDTO,
)

__all__ = [
    "PostCreateDTO",
    "PostUpdateDTO",
    "PostResponseDTO",
    "CommentCreateDTO",
    "CommentResponseDTO",
    "AuthorCreateDTO",
    "AuthorResponseDTO",
]
```

```python
# src/application/blog/dto/post_dto.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostCreateDTO(BaseModel):
    """DTO for creating a new post"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10, max_length=50000)
    slug: str = Field(..., regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    author_id: str
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = []
    category: Optional[str] = None

class PostUpdateDTO(BaseModel):
    """DTO for updating a post"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=10, max_length=50000)
    excerpt: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None

class PostResponseDTO(BaseModel):
    """DTO for post response"""
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
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
```

```python
# src/application/blog/dto/comment_dto.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentCreateDTO(BaseModel):
    """DTO for creating a comment"""
    author_name: str = Field(..., min_length=1, max_length=100)
    author_email: str
    content: str = Field(..., min_length=1, max_length=2000)

class CommentResponseDTO(BaseModel):
    """DTO for comment response"""
    id: str = Field(alias="_id")
    author_name: str
    author_email: str
    content: str
    status: str
    likes: int
    created_at: datetime
    
    class Config:
        populate_by_name = True
```

```python
# src/application/blog/dto/author_dto.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuthorCreateDTO(BaseModel):
    """DTO for creating an author"""
    email: str
    username: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class AuthorResponseDTO(BaseModel):
    """DTO for author response"""
    id: str = Field(alias="_id")
    email: str
    username: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
```

### 2.3 Application - Services

```python
# src/application/blog/services/__init__.py

from .post_service import PostApplicationService
from .comment_service import CommentApplicationService
from .author_service import AuthorApplicationService

__all__ = [
    "PostApplicationService",
    "CommentApplicationService",
    "AuthorApplicationService",
]
```

```python
# src/application/blog/services/post_service.py

from typing import List, Optional, Tuple
from bson import ObjectId
from datetime import datetime
from ...domain.blog.entities import Post
from ...domain.blog.repositories import PostRepository
from ...domain.blog.value_objects import Slug, PostStatus
from ...domain.blog.exceptions import PostExceptions
from ..dto import PostCreateDTO, PostUpdateDTO, PostResponseDTO

class PostApplicationService:
    """Post application service - orchestrates post use cases"""
    
    def __init__(self, post_repo: PostRepository, author_repo):
        self.post_repo = post_repo
        self.author_repo = author_repo
    
    async def create_post(self, dto: PostCreateDTO) -> Post:
        """Use case: Create a new blog post"""
        try:
            slug = Slug(dto.slug)
        except Exception as e:
            raise PostExceptions.InvalidPostStatusError("creation", str(e))
        
        # Get author
        author = await self.author_repo.get_by_id(ObjectId(dto.author_id))
        if not author:
            raise PostExceptions.PostNotFoundError(dto.author_id)
        
        # Create post aggregate
        post = Post(
            id=ObjectId(),
            slug=slug,
            title=dto.title,
            content=dto.content,
            excerpt=dto.excerpt,
            author_id=author.id,
            author_name=author.name,
            author_email=str(author.email),
            tags=dto.tags or [],
            category=dto.category
        )
        
        # Save to repository
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def publish_post(self, post_id: ObjectId) -> Post:
        """Use case: Publish a draft post"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostExceptions.PostNotFoundError(post_id)
        
        # Enforce business rule
        post.publish()
        
        # Persist changes
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def archive_post(self, post_id: ObjectId) -> Post:
        """Use case: Archive a published post"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostExceptions.PostNotFoundError(post_id)
        
        post.archive()
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def get_published_posts(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[Post], int]:
        """Use case: Retrieve published posts"""
        posts = await self.post_repo.find_published(skip, limit)
        count = await self.post_repo.count_published()
        return posts, count
    
    async def get_posts_by_tag(
        self,
        tag: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Post]:
        """Use case: Get posts by tag"""
        return await self.post_repo.find_by_tag(tag, skip, limit)
    
    async def update_post(
        self,
        post_id: ObjectId,
        dto: PostUpdateDTO
    ) -> Post:
        """Use case: Update post content"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostExceptions.PostNotFoundError(post_id)
        
        # Update content
        post.update_content(
            title=dto.title or post.title,
            content=dto.content or post.content,
            excerpt=dto.excerpt,
            tags=dto.tags,
            category=dto.category
        )
        
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def delete_post(self, post_id: ObjectId) -> bool:
        """Use case: Delete a post"""
        return await self.post_repo.delete(post_id)
```

```python
# src/application/blog/services/comment_service.py

from typing import Optional
from bson import ObjectId
from ...domain.blog.entities import Post, Comment
from ...domain.blog.repositories import PostRepository
from ...domain.blog.value_objects import CommentStatus
from ...domain.blog.exceptions import PostExceptions, CommentExceptions
from ..dto import CommentCreateDTO

class CommentApplicationService:
    """Comment application service"""
    
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo
    
    async def add_comment(
        self,
        post_id: ObjectId,
        dto: CommentCreateDTO
    ) -> Post:
        """Use case: Add comment to published post"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostExceptions.PostNotFoundError(post_id)
        
        # Create comment
        comment = Comment(
            author_name=dto.author_name,
            author_email=dto.author_email,
            content=dto.content,
            status=CommentStatus.PENDING
        )
        
        # Enforce business rule
        post.add_comment(comment)
        
        # Persist changes
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def approve_comment(
        self,
        post_id: ObjectId,
        comment_id: ObjectId
    ) -> Post:
        """Use case: Approve pending comment"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostExceptions.PostNotFoundError(post_id)
        
        # Find comment
        comment = next((c for c in post.comments if c.id == comment_id), None)
        if not comment:
            raise CommentExceptions.CommentNotFoundError(comment_id)
        
        # Approve
        comment.approve()
        
        # Persist
        saved_post = await self.post_repo.save(post)
        return saved_post
    
    async def remove_comment(
        self,
        post_id: ObjectId,
        comment_id: ObjectId
    ) -> bool:
        """Use case: Remove comment from post"""
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostExceptions.PostNotFoundError(post_id)
        
        removed = post.remove_comment(comment_id)
        if removed:
            await self.post_repo.save(post)
        
        return removed
```

```python
# src/application/blog/services/author_service.py

from typing import Optional
from bson import ObjectId
from ...domain.blog.entities import Author
from ...domain.blog.repositories import AuthorRepository
from ...domain.blog.value_objects import Email
from ...domain.blog.exceptions import AuthorExceptions
from ..dto import AuthorCreateDTO

class AuthorApplicationService:
    """Author application service"""
    
    def __init__(self, author_repo: AuthorRepository):
        self.author_repo = author_repo
    
    async def create_author(self, dto: AuthorCreateDTO) -> Author:
        """Use case: Create a new author"""
        # Validate email
        try:
            email = Email(dto.email)
        except Exception:
            raise AuthorExceptions.DuplicateEmailError(dto.email)
        
        # Check if author exists
        existing = await self.author_repo.get_by_email(email)
        if existing:
            raise AuthorExceptions.DuplicateEmailError(dto.email)
        
        existing_username = await self.author_repo.get_by_username(dto.username)
        if existing_username:
            raise AuthorExceptions.DuplicateUsernameError(dto.username)
        
        # Create author
        author = Author(
            id=ObjectId(),
            email=email,
            username=dto.username,
            name=dto.name,
            bio=dto.bio,
            avatar_url=dto.avatar_url
        )
        
        saved_author = await self.author_repo.save(author)
        return saved_author
    
    async def get_author(self, author_id: ObjectId) -> Optional[Author]:
        """Use case: Get author by ID"""
        return await self.author_repo.get_by_id(author_id)
```

```python
# src/application/blog/__init__.py

from .services import (
    PostApplicationService,
    CommentApplicationService,
    AuthorApplicationService,
)
from .dto import (
    PostCreateDTO,
    PostUpdateDTO,
    PostResponseDTO,
    CommentCreateDTO,
    CommentResponseDTO,
    AuthorCreateDTO,
    AuthorResponseDTO,
)

__all__ = [
    "PostApplicationService",
    "CommentApplicationService",
    "AuthorApplicationService",
    "PostCreateDTO",
    "PostUpdateDTO",
    "PostResponseDTO",
    "CommentCreateDTO",
    "CommentResponseDTO",
    "AuthorCreateDTO",
    "AuthorResponseDTO",
]
```

---

## 3. Infrastructure Layer - Multi-File Structure

### 3.1 Complete Infrastructure Directory Structure

```
src/infrastructure/
├── __init__.py
├── mongo/
│   ├── __init__.py
│   ├── database.py          # Connection setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── post_model.py    # Post Pydantic models
│   │   ├── author_model.py  # Author Pydantic models
│   │   └── comment_model.py # Comment Pydantic models
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── post_repository.py    # MongoPostRepository
│   │   ├── author_repository.py  # MongoAuthorRepository
│   │   └── tag_repository.py     # MongoTagRepository
│   │
│   └── migrations/
│       ├── __init__.py
│       └── migration_runner.py
│
├── cache/
│   ├── __init__.py
│   └── cache_manager.py     # Optional: Redis caching
│
└── dependencies.py          # FastAPI dependency injection
```

### 3.2 Infrastructure - MongoDB Models

```python
# src/infrastructure/mongo/models/__init__.py

from .post_model import PostModel, CommentModel
from .author_model import AuthorModel
from .comment_model import PyObjectId

__all__ = [
    "PostModel",
    "CommentModel",
    "AuthorModel",
    "PyObjectId",
]
```

```python
# src/infrastructure/mongo/models/post_model.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class CommentModel(BaseModel):
    """Pydantic model for comment embedded in post"""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
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
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    slug: str
    title: str
    content: str
    excerpt: Optional[str] = None
    author_id: Optional[str] = None
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
```

```python
# src/infrastructure/mongo/models/author_model.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class AuthorModel(BaseModel):
    """Pydantic model for Author in MongoDB"""
    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
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

### 3.3 Infrastructure - Repositories

```python
# src/infrastructure/mongo/repositories/__init__.py

from .post_repository import MongoPostRepository
from .author_repository import MongoAuthorRepository
from .tag_repository import MongoTagRepository

__all__ = [
    "MongoPostRepository",
    "MongoAuthorRepository",
    "MongoTagRepository",
]
```

```python
# src/infrastructure/mongo/repositories/post_repository.py

from typing import List, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ....domain.blog.entities import Post, Comment
from ....domain.blog.repositories import PostRepository
from ....domain.blog.value_objects import Slug, PostStatus, CommentStatus
from ..models import PostModel, CommentModel

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
        return self._to_post_entity(result) if result else None
    
    async def get_by_slug(self, slug: Slug) -> Optional[Post]:
        """Get post by slug"""
        result = await self.collection.find_one({"slug": str(slug)})
        return self._to_post_entity(result) if result else None
    
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
    
    async def find_by_author(self, author_id: ObjectId, skip: int = 0, limit: int = 10) -> List[Post]:
        """Find posts by author"""
        cursor = self.collection.find(
            {"author_id": author_id}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
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

```python
# src/infrastructure/mongo/repositories/author_repository.py

from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from ....domain.blog.entities import Author
from ....domain.blog.repositories import AuthorRepository
from ....domain.blog.value_objects import Email

class MongoAuthorRepository(AuthorRepository):
    """MongoDB implementation of AuthorRepository"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["authors"]
    
    async def save(self, author: Author) -> Author:
        """Save author"""
        author_data = {
            "_id": author.id,
            "email": str(author.email),
            "username": author.username,
            "name": author.name,
            "bio": author.bio,
            "avatar_url": author.avatar_url,
            "created_at": author.created_at,
            "updated_at": author.updated_at,
        }
        
        await self.collection.update_one(
            {"_id": author.id},
            {"$set": author_data},
            upsert=True
        )
        return author
    
    async def get_by_id(self, author_id: ObjectId) -> Optional[Author]:
        """Get author by ID"""
        result = await self.collection.find_one({"_id": author_id})
        return self._to_author_entity(result) if result else None
    
    async def get_by_email(self, email: Email) -> Optional[Author]:
        """Get author by email"""
        result = await self.collection.find_one({"email": str(email)})
        return self._to_author_entity(result) if result else None
    
    async def get_by_username(self, username: str) -> Optional[Author]:
        """Get author by username"""
        result = await self.collection.find_one({"username": username})
        return self._to_author_entity(result) if result else None
    
    async def delete(self, author_id: ObjectId) -> bool:
        """Delete author"""
        result = await self.collection.delete_one({"_id": author_id})
        return result.deleted_count > 0
    
    def _to_author_entity(self, doc: dict) -> Author:
        """Convert MongoDB document to Author entity"""
        return Author(
            id=doc["_id"],
            email=Email(doc["email"]),
            username=doc["username"],
            name=doc["name"],
            bio=doc.get("bio"),
            avatar_url=doc.get("avatar_url"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"]
        )
```

### 3.4 Infrastructure - Database Setup

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
        
        # Create indexes for posts
        await posts_collection.create_index("slug", unique=True)
        await posts_collection.create_index("status")
        await posts_collection.create_index("published_at")
        await posts_collection.create_index("tags")
        await posts_collection.create_index("author_id")
        await posts_collection.create_index([("status", 1), ("published_at", -1)])
        
        # Create indexes for authors
        authors_collection = cls.db["authors"]
        await authors_collection.create_index("email", unique=True)
        await authors_collection.create_index("username", unique=True)
        
        # Create indexes for tags
        tags_collection = cls.db["tags"]
        await tags_collection.create_index("slug", unique=True)

def get_database() -> AsyncIOMotorDatabase:
    """Dependency: Get MongoDB database"""
    return MongoDatabase.db
```

```python
# src/infrastructure/__init__.py

from .mongo.database import MongoDatabase, get_database
from .mongo.repositories import (
    MongoPostRepository,
    MongoAuthorRepository,
    MongoTagRepository,
)

__all__ = [
    "MongoDatabase",
    "get_database",
    "MongoPostRepository",
    "MongoAuthorRepository",
    "MongoTagRepository",
]
```

### 3.5 Infrastructure - Dependencies

```python
# src/infrastructure/dependencies.py

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .mongo.database import get_database
from .mongo.repositories import MongoPostRepository, MongoAuthorRepository
from ..application.blog.services import (
    PostApplicationService,
    CommentApplicationService,
    AuthorApplicationService,
)

# Repository dependencies
async def get_post_repository(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> MongoPostRepository:
    """Dependency: Get post repository"""
    return MongoPostRepository(db)

async def get_author_repository(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> MongoAuthorRepository:
    """Dependency: Get author repository"""
    return MongoAuthorRepository(db)

# Service dependencies
async def get_post_service(
    post_repo: MongoPostRepository = Depends(get_post_repository),
    author_repo: MongoAuthorRepository = Depends(get_author_repository)
) -> PostApplicationService:
    """Dependency: Get post application service"""
    return PostApplicationService(post_repo, author_repo)

async def get_comment_service(
    post_repo: MongoPostRepository = Depends(get_post_repository)
) -> CommentApplicationService:
    """Dependency: Get comment application service"""
    return CommentApplicationService(post_repo)

async def get_author_service(
    author_repo: MongoAuthorRepository = Depends(get_author_repository)
) -> AuthorApplicationService:
    """Dependency: Get author application service"""
    return AuthorApplicationService(author_repo)
```

---

## 4. Presentation Layer - Multi-File Structure

### 4.1 Complete Presentation Directory Structure

```
src/presentation/
├── __init__.py
├── routers/
│   ├── __init__.py
│   ├── posts.py         # Post routes
│   ├── comments.py      # Comment routes
│   ├── authors.py       # Author routes
│   └── tags.py          # Tag routes
│
├── schemas/
│   ├── __init__.py
│   ├── post_schemas.py  # Post request/response schemas
│   ├── comment_schemas.py # Comment schemas
│   └── author_schemas.py  # Author schemas
│
├── exception_handlers.py # Exception handlers
└── middleware/
    ├── __init__.py
    └── error_middleware.py
```

### 4.2 Presentation - Schemas

```python
# src/presentation/schemas/__init__.py

from .post_schemas import PostCreateSchema, PostResponseSchema, PostUpdateSchema
from .comment_schemas import CommentCreateSchema, CommentResponseSchema
from .author_schemas import AuthorCreateSchema, AuthorResponseSchema

__all__ = [
    "PostCreateSchema",
    "PostResponseSchema",
    "PostUpdateSchema",
    "CommentCreateSchema",
    "CommentResponseSchema",
    "AuthorCreateSchema",
    "AuthorResponseSchema",
]
```

```python
# src/presentation/schemas/post_schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PostCreateSchema(BaseModel):
    """Schema for creating a post"""
    title: str = Field(..., min_length=1, max_length=255, description="Post title")
    content: str = Field(..., min_length=10, max_length=50000, description="Post content")
    slug: str = Field(..., regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$', description="URL slug")
    author_id: str = Field(..., description="Author ID")
    excerpt: Optional[str] = Field(None, max_length=500, description="Post excerpt")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")
    category: Optional[str] = Field(None, description="Category")

class PostUpdateSchema(BaseModel):
    """Schema for updating a post"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=10, max_length=50000)
    excerpt: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    category: Optional[str] = None

class CommentSchema(BaseModel):
    """Schema for comment in post response"""
    id: str = Field(alias="_id")
    author_name: str
    author_email: str
    content: str
    status: str
    likes: int
    created_at: datetime
    
    class Config:
        populate_by_name = True

class PostResponseSchema(BaseModel):
    """Schema for post response"""
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
    comments: List[CommentSchema] = []
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
```

```python
# src/presentation/schemas/comment_schemas.py

from pydantic import BaseModel, Field
from datetime import datetime

class CommentCreateSchema(BaseModel):
    """Schema for creating a comment"""
    author_name: str = Field(..., min_length=1, max_length=100)
    author_email: str = Field(...)
    content: str = Field(..., min_length=1, max_length=2000)

class CommentResponseSchema(BaseModel):
    """Schema for comment response"""
    id: str = Field(alias="_id")
    author_name: str
    author_email: str
    content: str
    status: str
    likes: int
    created_at: datetime
    
    class Config:
        populate_by_name = True
```

```python
# src/presentation/schemas/author_schemas.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuthorCreateSchema(BaseModel):
    """Schema for creating an author"""
    email: str = Field(..., description="Author email")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    bio: Optional[str] = Field(None, description="Author bio")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")

class AuthorResponseSchema(BaseModel):
    """Schema for author response"""
    id: str = Field(alias="_id")
    email: str
    username: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
```

### 4.3 Presentation - Routes

```python
# src/presentation/routers/__init__.py

from .posts import router as posts_router
from .comments import router as comments_router
from .authors import router as authors_router

__all__ = [
    "posts_router",
    "comments_router",
    "authors_router",
]
```

```python
# src/presentation/routers/posts.py

from fastapi import APIRouter, HTTPException, Depends, Query, status
from bson import ObjectId
from ...application.blog.services import PostApplicationService
from ...application.blog.dto import PostCreateDTO, PostUpdateDTO
from ...infrastructure.dependencies import get_post_service
from ...domain.blog.exceptions import PostExceptions
from ..schemas import PostCreateSchema, PostUpdateSchema, PostResponseSchema

router = APIRouter(prefix="/api/v1/posts", tags=["posts"])

@router.post(
    "",
    response_model=PostResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blog post"
)
async def create_post(
    request: PostCreateSchema,
    service: PostApplicationService = Depends(get_post_service)
):
    """Create a new blog post"""
    try:
        dto = PostCreateDTO(**request.dict())
        post = await service.create_post(dto)
        return post.__dict__
    except PostExceptions.PostException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "",
    response_model=dict,
    summary="Get published posts"
)
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: PostApplicationService = Depends(get_post_service)
):
    """Get published posts with pagination"""
    try:
        posts, total = await service.get_published_posts(skip, limit)
        return {
            "items": [p.__dict__ for p in posts],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}", response_model=PostResponseSchema)
async def get_post(
    post_id: str,
    service: PostApplicationService = Depends(get_post_service)
):
    """Get a specific post by ID"""
    try:
        post = await service.post_repo.get_by_id(ObjectId(post_id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post.record_view()
        await service.post_repo.save(post)
        return post.__dict__
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{post_id}/publish", response_model=PostResponseSchema)
async def publish_post(
    post_id: str,
    service: PostApplicationService = Depends(get_post_service)
):
    """Publish a draft post"""
    try:
        post = await service.publish_post(ObjectId(post_id))
        return post.__dict__
    except PostExceptions.PostException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{post_id}", response_model=PostResponseSchema)
async def update_post(
    post_id: str,
    request: PostUpdateSchema,
    service: PostApplicationService = Depends(get_post_service)
):
    """Update a post"""
    try:
        dto = PostUpdateDTO(**request.dict(exclude_unset=True))
        post = await service.update_post(ObjectId(post_id), dto)
        return post.__dict__
    except PostExceptions.PostException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    service: PostApplicationService = Depends(get_post_service)
):
    """Delete a post"""
    try:
        success = await service.delete_post(ObjectId(post_id))
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tag/{tag}")
async def get_posts_by_tag(
    tag: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: PostApplicationService = Depends(get_post_service)
):
    """Get posts by tag"""
    try:
        posts = await service.get_posts_by_tag(tag, skip, limit)
        return {"items": [p.__dict__ for p in posts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# src/presentation/routers/comments.py

from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from ...application.blog.services import CommentApplicationService
from ...application.blog.dto import CommentCreateDTO
from ...infrastructure.dependencies import get_comment_service
from ...domain.blog.exceptions import PostExceptions, CommentExceptions
from ..schemas import CommentCreateSchema, PostResponseSchema

router = APIRouter(prefix="/api/v1/posts/{post_id}/comments", tags=["comments"])

@router.post(
    "",
    response_model=PostResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to post"
)
async def add_comment(
    post_id: str,
    request: CommentCreateSchema,
    service: CommentApplicationService = Depends(get_comment_service)
):
    """Add a comment to a published post"""
    try:
        dto = CommentCreateDTO(**request.dict())
        post = await service.add_comment(ObjectId(post_id), dto)
        return post.__dict__
    except PostExceptions.PostException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{comment_id}/approve", response_model=PostResponseSchema)
async def approve_comment(
    post_id: str,
    comment_id: str,
    service: CommentApplicationService = Depends(get_comment_service)
):
    """Approve a pending comment"""
    try:
        post = await service.approve_comment(ObjectId(post_id), ObjectId(comment_id))
        return post.__dict__
    except (PostExceptions.PostException, CommentExceptions.CommentException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_comment(
    post_id: str,
    comment_id: str,
    service: CommentApplicationService = Depends(get_comment_service)
):
    """Remove a comment from post"""
    try:
        success = await service.remove_comment(ObjectId(post_id), ObjectId(comment_id))
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

```python
# src/presentation/routers/authors.py

from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from ...application.blog.services import AuthorApplicationService
from ...application.blog.dto import AuthorCreateDTO
from ...infrastructure.dependencies import get_author_service
from ...domain.blog.exceptions import AuthorExceptions
from ..schemas import AuthorCreateSchema, AuthorResponseSchema

router = APIRouter(prefix="/api/v1/authors", tags=["authors"])

@router.post(
    "",
    response_model=AuthorResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new author"
)
async def create_author(
    request: AuthorCreateSchema,
    service: AuthorApplicationService = Depends(get_author_service)
):
    """Create a new author"""
    try:
        dto = AuthorCreateDTO(**request.dict())
        author = await service.create_author(dto)
        return author.__dict__
    except AuthorExceptions.AuthorException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{author_id}", response_model=AuthorResponseSchema)
async def get_author(
    author_id: str,
    service: AuthorApplicationService = Depends(get_author_service)
):
    """Get author by ID"""
    try:
        author = await service.get_author(ObjectId(author_id))
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
        return author.__dict__
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 5. Import Organization Best Practices

### 5.1 __init__.py Files - Re-export Pattern

```python
# src/domain/__init__.py

from .blog import (
    Author,
    Comment,
    Post,
    Email,
    Slug,
    PostStatus,
    CommentStatus,
    PostRepository,
    AuthorRepository,
    TagRepository,
)

__all__ = [
    "Author",
    "Comment",
    "Post",
    "Email",
    "Slug",
    "PostStatus",
    "CommentStatus",
    "PostRepository",
    "AuthorRepository",
    "TagRepository",
]
```

```python
# src/application/__init__.py

from .blog import (
    PostApplicationService,
    CommentApplicationService,
    AuthorApplicationService,
    PostCreateDTO,
    PostUpdateDTO,
    PostResponseDTO,
)

__all__ = [
    "PostApplicationService",
    "CommentApplicationService",
    "AuthorApplicationService",
    "PostCreateDTO",
    "PostUpdateDTO",
    "PostResponseDTO",
]
```

### 5.2 Avoiding Circular Imports

```python
# ✅ GOOD: Dependencies flow downward
# domain/ (no dependencies)
#   └── application/ (depends on domain)
#       └── infrastructure/ (depends on domain & application)
#           └── presentation/ (depends on all above)

# ❌ BAD: Circular dependency
# domain/
#   └── application/ (imports from domain)
#       └── domain/ (imports from application) ❌ CIRCULAR!
```

---

## 6. Benefits & Best Practices

### 6.1 Benefits of Multi-File Structure

| Benefit | Explanation |
|---------|-------------|
| **Maintainability** | Find files quickly, easier to understand module purpose |
| **Scalability** | Add new domains/features without cluttering existing files |
| **Testing** | Test specific modules independently with focused test files |
| **Collaboration** | Multiple developers can work without merge conflicts |
| **Reusability** | Import only what you need from each module |
| **Import Management** | Clear dependencies between layers |

### 6.2 File Organization Principles

1. **Single Responsibility**: Each file has one clear purpose
2. **Package Organization**: Group related files in packages
3. **Import Order**: Standard library → Third-party → Local
4. **Circular Dependencies**: Avoid by respecting layer boundaries
5. **__init__.py Files**: Use for public API and re-exports

### 6.3 Naming Conventions

```python
# Modules and files follow pattern:
# {domain}_{type}.py

# Examples:
post_service.py         # Service for posts
post_repository.py      # Repository for posts
post_exceptions.py      # Exceptions for posts
post_dto.py             # DTOs for posts
post_schemas.py         # Pydantic schemas for posts
post_entity.py          # Entity definition
post_value_objects.py   # Value objects
```

---

## Migration Guide: From Monolithic to Multi-File

### Step 1: Create Directory Structure
```bash
mkdir -p src/domain/blog/{entities,value_objects,repositories,exceptions}
mkdir -p src/application/blog/{services,dto,use_cases}
mkdir -p src/infrastructure/mongo/{models,repositories,migrations}
mkdir -p src/presentation/{routers,schemas,middleware}
```

### Step 2: Move Code to New Files
- Start with domain layer (no dependencies)
- Move to application layer
- Then infrastructure
- Finally presentation

### Step 3: Update Imports
- Update all imports to reflect new file locations
- Use relative imports within packages
- Use absolute imports from src/

### Step 4: Create __init__.py Files
- Add re-export statements
- Define public API for each package
- Import fixtures for easier access

### Step 5: Test
- Run unit tests
- Check all imports work
- Verify no circular dependencies

---

This structured approach makes your codebase professional, maintainable, and ready for team collaboration and scaling.
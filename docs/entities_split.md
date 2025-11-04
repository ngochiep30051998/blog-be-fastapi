# Tách Entities.py thành File Riêng Biệt

Hướng dẫn chi tiết về cách tổ chức entities.py thành các file riêng để codebase dễ bảo trì hơn.

---

## Cấu Trúc Thư Mục Được Khuyến Nghị

```
src/domain/blog/
├── __init__.py
├── entities/
│   ├── __init__.py
│   ├── author.py          # Author entity
│   ├── comment.py         # Comment entity
│   ├── post.py            # Post aggregate root
│   ├── category.py        # Category entity
│   └── tag.py             # Tag entity
├── value_objects.py       # (giữ nguyên)
├── repositories.py        # (giữ nguyên)
└── exceptions.py          # (giữ nguyên)
```

---

## 1. Author Entity

File: `src/domain/blog/entities/author.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from ..value_objects import Email

@dataclass
class Author:
    """
    Author entity - Đại diện cho một tác giả blog
    
    Là một aggregate root trong bounded context Blog
    Một tác giả có thể viết nhiều bài viết
    """
    id: ObjectId
    email: Email
    username: str
    name: str
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __eq__(self, other):
        """Hai author bằng nhau nếu có cùng ID"""
        return isinstance(other, Author) and self.id == other.id
    
    def __hash__(self):
        """Cho phép Author được sử dụng trong set/dict"""
        return hash(self.id)
    
    def update_profile(self, name: str, bio: str | None = None, avatar_url: str | None = None):
        """
        Business rule: Cập nhật thông tin tác giả
        
        Args:
            name: Tên mới của tác giả
            bio: Tiểu sử (tùy chọn)
            avatar_url: URL avatar (tùy chọn)
        """
        self.name = name
        if bio is not None:
            self.bio = bio
        if avatar_url is not None:
            self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()
    
    def update_email(self, email: Email):
        """
        Business rule: Cập nhật email tác giả
        
        Email phải là Email value object hợp lệ
        """
        if not isinstance(email, Email):
            raise TypeError("Email must be an Email value object")
        self.email = email
        self.updated_at = datetime.utcnow()
```

---

## 2. Comment Entity

File: `src/domain/blog/entities/comment.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from enum import Enum

class CommentStatus(str, Enum):
    """Trạng thái của comment"""
    PENDING = "pending"
    APPROVED = "approved"
    SPAM = "spam"

@dataclass
class Comment:
    """
    Comment entity - Nhận xét trên bài viết
    
    Comment là một value object được nhúng trong Post aggregate
    Không tồn tại độc lập, luôn là một phần của Post
    """
    id: ObjectId = field(default_factory=ObjectId)
    author_name: str = field(min_length=1)
    author_email: str = field(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    content: str = field(min_length=1, max_length=5000)
    status: CommentStatus = CommentStatus.PENDING
    likes: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate comment data"""
        self._validate()
    
    def _validate(self):
        """Validate business rules"""
        if len(self.author_name) < 1:
            raise ValueError("Author name cannot be empty")
        if len(self.author_name) > 100:
            raise ValueError("Author name cannot exceed 100 characters")
        if len(self.content) < 1:
            raise ValueError("Content cannot be empty")
        if len(self.content) > 5000:
            raise ValueError("Content cannot exceed 5000 characters")
    
    def approve(self):
        """
        Business rule: Phê duyệt comment
        
        Chỉ comment pending mới có thể được phê duyệt
        """
        if self.status != CommentStatus.PENDING:
            raise ValueError(
                f"Only pending comments can be approved. Current status: {self.status}"
            )
        self.status = CommentStatus.APPROVED
    
    def mark_as_spam(self):
        """
        Business rule: Đánh dấu comment là spam
        
        Bất kỳ comment nào cũng có thể bị đánh dấu là spam
        """
        self.status = CommentStatus.SPAM
    
    def add_like(self):
        """
        Business rule: Thêm like cho comment
        
        Tăng số lượt like
        """
        if self.likes < 0:
            raise ValueError("Likes count cannot be negative")
        self.likes += 1
    
    def is_visible(self) -> bool:
        """
        Business rule: Kiểm tra comment có hiển thị không
        
        Chỉ approved comments mới hiển thị công khai
        """
        return self.status == CommentStatus.APPROVED
```

---

## 3. Post Aggregate Root

File: `src/domain/blog/entities/post.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from bson import ObjectId
from enum import Enum
from .comment import Comment, CommentStatus
from ..value_objects import Slug, PostStatus

@dataclass
class Post:
    """
    Post aggregate root - Bài viết chính
    
    Post là aggregate root của blog domain
    Chứa Comments như một phần của aggregate
    Đảm bảo tất cả business rules đều được áp dụng
    """
    id: ObjectId
    slug: Slug
    title: str
    content: str
    excerpt: str | None = None
    author_id: ObjectId | None = None
    author_name: str | None = None
    author_email: str | None = None
    status: PostStatus = PostStatus.DRAFT
    tags: List[str] = field(default_factory=list)
    category: str | None = None
    views_count: int = 0
    likes_count: int = 0
    comments: List[Comment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: datetime | None = None
    
    def __post_init__(self):
        """Validate post data"""
        self._validate()
    
    def _validate(self):
        """Validate business rules"""
        if len(self.title) < 1:
            raise ValueError("Title cannot be empty")
        if len(self.title) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        if len(self.content) < 10:
            raise ValueError("Content must be at least 10 characters")
        if len(self.content) > 50000:
            raise ValueError("Content cannot exceed 50000 characters")
        if self.views_count < 0:
            raise ValueError("Views count cannot be negative")
        if self.likes_count < 0:
            raise ValueError("Likes count cannot be negative")
    
    def __eq__(self, other):
        """Hai post bằng nhau nếu có cùng ID"""
        return isinstance(other, Post) and self.id == other.id
    
    def __hash__(self):
        """Cho phép Post được sử dụng trong set/dict"""
        return hash(self.id)
    
    # ========== Business Rules ==========
    
    def publish(self):
        """
        Business rule: Xuất bản bài viết
        
        - Chỉ post ở trạng thái DRAFT mới có thể xuất bản
        - Sau khi xuất bản, published_at được set
        
        Raises:
            ValueError: Nếu post đã được xuất bản
        """
        if self.status == PostStatus.PUBLISHED:
            raise ValueError("Post is already published")
        
        self.status = PostStatus.PUBLISHED
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def unpublish(self):
        """
        Business rule: Thu hồi xuất bản bài viết
        
        Chuyển bài viết về trạng thái DRAFT
        """
        if self.status == PostStatus.DRAFT:
            raise ValueError("Post is already in draft status")
        
        self.status = PostStatus.DRAFT
        self.published_at = None
        self.updated_at = datetime.utcnow()
    
    def add_comment(self, comment: Comment) -> None:
        """
        Business rule: Thêm comment vào bài viết
        
        - Chỉ có thể thêm comment vào post đã xuất bản
        - Comment mới có status là PENDING
        
        Args:
            comment: Comment object được thêm vào
            
        Raises:
            ValueError: Nếu post chưa được xuất bản
        """
        if self.status != PostStatus.PUBLISHED:
            raise ValueError(
                "Cannot add comments to unpublished posts. "
                f"Current status: {self.status}"
            )
        
        if comment.status not in [CommentStatus.PENDING, CommentStatus.APPROVED]:
            raise ValueError(
                f"Invalid comment status: {comment.status}. "
                "New comments must be PENDING or APPROVED"
            )
        
        self.comments.append(comment)
        self.updated_at = datetime.utcnow()
    
    def remove_comment(self, comment_id: ObjectId) -> bool:
        """
        Business rule: Xóa comment khỏi bài viết
        
        Args:
            comment_id: ID của comment cần xóa
            
        Returns:
            True nếu xóa thành công, False nếu không tìm thấy
        """
        original_length = len(self.comments)
        self.comments = [c for c in self.comments if c.id != comment_id]
        
        if len(self.comments) < original_length:
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_approved_comments(self) -> List[Comment]:
        """
        Business rule: Lấy danh sách approved comments
        
        Chỉ trả về comments đã được phê duyệt
        """
        return [c for c in self.comments if c.status == CommentStatus.APPROVED]
    
    def get_pending_comments(self) -> List[Comment]:
        """
        Business rule: Lấy danh sách pending comments
        
        Dùng cho admin review
        """
        return [c for c in self.comments if c.status == CommentStatus.PENDING]
    
    def record_view(self) -> None:
        """
        Business rule: Ghi nhận lượt xem
        
        Tăng views_count khi có người xem bài viết
        """
        if self.status != PostStatus.PUBLISHED:
            raise ValueError("Cannot record view for unpublished posts")
        
        self.views_count += 1
    
    def like(self) -> None:
        """
        Business rule: Like bài viết
        
        Tăng likes_count khi có người like
        """
        self.likes_count += 1
    
    def update_content(
        self,
        title: str | None = None,
        content: str | None = None,
        excerpt: str | None = None
    ):
        """
        Business rule: Cập nhật nội dung bài viết
        
        - Cho phép cập nhật cả draft và published posts
        - Cập nhật updated_at
        - Không thay đổi published_at
        
        Args:
            title: Tiêu đề mới (tùy chọn)
            content: Nội dung mới (tùy chọn)
            excerpt: Trích dẫn mới (tùy chọn)
            
        Raises:
            ValueError: Nếu dữ liệu không hợp lệ
        """
        if title is not None:
            if len(title) < 1:
                raise ValueError("Title cannot be empty")
            if len(title) > 255:
                raise ValueError("Title cannot exceed 255 characters")
            self.title = title
        
        if content is not None:
            if len(content) < 10:
                raise ValueError("Content must be at least 10 characters")
            if len(content) > 50000:
                raise ValueError("Content cannot exceed 50000 characters")
            self.content = content
        
        if excerpt is not None:
            if len(excerpt) > 500:
                raise ValueError("Excerpt cannot exceed 500 characters")
            self.excerpt = excerpt
        
        self.updated_at = datetime.utcnow()
    
    def add_tags(self, tags: List[str]) -> None:
        """
        Business rule: Thêm tags cho bài viết
        
        Args:
            tags: Danh sách tags mới
        """
        if not isinstance(tags, list):
            raise TypeError("Tags must be a list")
        
        # Validate each tag
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError(f"Tag must be string, got {type(tag)}")
            if len(tag) < 1:
                raise ValueError("Tag cannot be empty")
            if len(tag) > 50:
                raise ValueError("Tag cannot exceed 50 characters")
        
        # Merge with existing tags, avoiding duplicates
        self.tags = list(set(self.tags + tags))
        self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> bool:
        """
        Business rule: Xóa tag khỏi bài viết
        
        Args:
            tag: Tag cần xóa
            
        Returns:
            True nếu xóa thành công
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def set_category(self, category: str | None) -> None:
        """
        Business rule: Đặt category cho bài viết
        
        Args:
            category: Tên category (None để xóa)
        """
        if category is not None and len(category) < 1:
            raise ValueError("Category cannot be empty string")
        
        self.category = category
        self.updated_at = datetime.utcnow()
    
    def is_published(self) -> bool:
        """Kiểm tra bài viết đã được xuất bản chưa"""
        return self.status == PostStatus.PUBLISHED
    
    def can_receive_comments(self) -> bool:
        """Kiểm tra bài viết có thể nhận comments không"""
        return self.status == PostStatus.PUBLISHED
```

---

## 4. Category Entity

File: `src/domain/blog/entities/category.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from ..value_objects import Slug

@dataclass
class Category:
    """
    Category entity - Thể loại bài viết
    
    Đại diện cho một thể loại (ví dụ: Technology, Travel, etc.)
    Có slug duy nhất để sử dụng trong URL
    """
    id: ObjectId
    name: str
    slug: Slug
    description: str | None = None
    posts_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __eq__(self, other):
        """Hai category bằng nhau nếu có cùng ID"""
        return isinstance(other, Category) and self.id == other.id
    
    def __hash__(self):
        """Cho phép Category được sử dụng trong set/dict"""
        return hash(self.id)
    
    def update(
        self,
        name: str | None = None,
        description: str | None = None
    ):
        """
        Business rule: Cập nhật category
        
        Args:
            name: Tên mới (tùy chọn)
            description: Mô tả mới (tùy chọn)
        """
        if name is not None:
            if len(name) < 1:
                raise ValueError("Name cannot be empty")
            if len(name) > 100:
                raise ValueError("Name cannot exceed 100 characters")
            self.name = name
        
        if description is not None:
            if len(description) > 500:
                raise ValueError("Description cannot exceed 500 characters")
            self.description = description
        
        self.updated_at = datetime.utcnow()
    
    def increment_posts_count(self):
        """Tăng số lượng bài viết trong category"""
        self.posts_count += 1
    
    def decrement_posts_count(self):
        """Giảm số lượng bài viết trong category"""
        if self.posts_count > 0:
            self.posts_count -= 1
```

---

## 5. Tag Entity

File: `src/domain/blog/entities/tag.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from ..value_objects import Slug

@dataclass
class Tag:
    """
    Tag entity - Nhãn bài viết
    
    Đại diện cho một tag (ví dụ: python, fastapi, mongodb, etc.)
    Có slug duy nhất để sử dụng trong URL
    """
    id: ObjectId
    name: str
    slug: Slug
    description: str | None = None
    posts_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __eq__(self, other):
        """Hai tag bằng nhau nếu có cùng ID"""
        return isinstance(other, Tag) and self.id == other.id
    
    def __hash__(self):
        """Cho phép Tag được sử dụng trong set/dict"""
        return hash(self.id)
    
    def update(
        self,
        name: str | None = None,
        description: str | None = None
    ):
        """
        Business rule: Cập nhật tag
        
        Args:
            name: Tên mới (tùy chọn)
            description: Mô tả mới (tùy chọn)
        """
        if name is not None:
            if len(name) < 1:
                raise ValueError("Name cannot be empty")
            if len(name) > 50:
                raise ValueError("Name cannot exceed 50 characters")
            self.name = name
        
        if description is not None:
            if len(description) > 500:
                raise ValueError("Description cannot exceed 500 characters")
            self.description = description
        
        self.updated_at = datetime.utcnow()
    
    def increment_posts_count(self):
        """Tăng số lượng bài viết có tag này"""
        self.posts_count += 1
    
    def decrement_posts_count(self):
        """Giảm số lượng bài viết có tag này"""
        if self.posts_count > 0:
            self.posts_count -= 1
```

---

## 6. __init__.py cho Entities Package

File: `src/domain/blog/entities/__init__.py`

```python
"""
Blog domain entities package

Export tất cả entities để dễ import từ ngoài package
"""

from .author import Author
from .comment import Comment, CommentStatus
from .post import Post
from .category import Category
from .tag import Tag

__all__ = [
    "Author",
    "Comment",
    "CommentStatus",
    "Post",
    "Category",
    "Tag",
]
```

---

## 7. Cập Nhật Value Objects

File: `src/domain/blog/value_objects.py` (cập nhật import)

```python
# ... existing code ...

# Có thể import CommentStatus từ entities nếu cần
from .entities import CommentStatus  # Optional, vì đã import ở __init__.py

# Hoặc giữ PostStatus ở value_objects.py
class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"

# ... rest of existing code ...
```

---

## 8. Cách Import từ Các File Khác

### Từ Application Layer

```python
# src/application/blog/services.py

from ...domain.blog.entities import Post, Comment, Author, Category, Tag
from ...domain.blog.value_objects import Slug, Email, PostStatus

class PostApplicationService:
    async def create_post(self, ...):
        post = Post(
            id=ObjectId(),
            slug=Slug(slug_str),
            title=title,
            content=content,
            ...
        )
        return post
```

### Từ Infrastructure Layer

```python
# src/infrastructure/mongo/repositories.py

from ...domain.blog.entities import Post, Comment, Author
from ...domain.blog.value_objects import PostStatus, CommentStatus

class MongoPostRepository(PostRepository):
    def _to_post_entity(self, doc: dict) -> Post:
        comments = [
            Comment(
                id=c["_id"],
                author_name=c["author_name"],
                ...
            )
            for c in doc.get("comments", [])
        ]
        return Post(...)
```

### Từ Presentation Layer

```python
# src/presentation/routers/blog.py

from ...domain.blog.entities import Post, Comment
from ...domain.blog.value_objects import PostStatus

@router.post("")
async def create_post(request: PostCreateRequest, ...):
    post = await service.create_post(...)
    return post
```

---

## 9. Cấu Trúc Đầy Đủ Sau Tách Nhỏ

```
personal-blog/
├── src/
│   ├── domain/
│   │   └── blog/
│   │       ├── __init__.py
│   │       ├── entities/
│   │       │   ├── __init__.py
│   │       │   ├── author.py
│   │       │   ├── comment.py
│   │       │   ├── post.py
│   │       │   ├── category.py
│   │       │   └── tag.py
│   │       ├── value_objects.py
│   │       ├── repositories.py
│   │       └── exceptions.py
│   ├── application/
│   ├── infrastructure/
│   ├── presentation/
│   └── core/
└── tests/
```

---

## 10. Lợi Ích của Việc Tách Nhỏ

✅ **Single Responsibility**: Mỗi entity file chỉ focus một entity
✅ **Dễ Bảo Trì**: Dễ tìm và sửa lỗi entity cụ thể
✅ **Dễ Test**: Unit test từng entity độc lập
✅ **Tái Sử Dụng**: Import chỉ những gì cần thiết
✅ **Sẵn Sàng Mở Rộng**: Dễ thêm business logic mới
✅ **Git History Sạch**: Conflicts ít hơn khi merge
✅ **Code Review**: Dễ review từng entity

---

## 11. Tips Khi Tách Nhỏ

1. **Giữ dependencies tối thiểu**: Không circular imports
2. **Docstrings chi tiết**: Mô tả rõ business logic của entity
3. **Type hints đầy đủ**: Python 3.10+ union types (|)
4. **Validate trong __post_init__**: Đảm bảo invariants
5. **Business methods có tên rõ ràng**: `publish()` không `change_status()`
6. **Exceptions cụ thể**: Không dùng generic Exception

---

Sau khi tách, codebase của bạn sẽ sạch hơn, dễ bảo trì hơn, và sẵn sàng cho việc phát triển tính năng mới!
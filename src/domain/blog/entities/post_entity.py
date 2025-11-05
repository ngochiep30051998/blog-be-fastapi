from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from src.domain.blog.value_objects.slug import Slug
from src.domain.blog.value_objects.statuses import PostStatus

@dataclass
class Post:
    """Post aggregate root"""
    id: ObjectId
    slug: Slug
    title: str
    content: str
    excerpt: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    views_count: int = 0
    likes_count: int = 0
    # comments: List[Comment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

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
    
    # def add_comment(self, comment: Comment) -> None:
    #     """Business rule: Add comment to post"""
    #     if self.status != PostStatus.PUBLISHED:
    #         raise ValueError("Cannot add comments to unpublished posts")
    #     if comment.status not in [CommentStatus.PENDING, CommentStatus.APPROVED]:
    #         raise ValueError("Invalid comment status for new comments")
    #     self.comments.append(comment)
    
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
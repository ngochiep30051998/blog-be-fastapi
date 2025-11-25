from typing import Tuple
from bson import ObjectId
from src.core.value_objects.slug import Slug
from src.core.value_objects.statuses import PostStatus
from src.domain.posts.entity import PostEntity
from src.infrastructure.mongo.post_repository_impl import MongoPostRepository
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from src.infrastructure.mongo.tag_repository_impl import MongoTagRepository
from src.application.services.tag_service import TagService
from src.application.dto.post_dto import TagInput

class PostService:
    def __init__(self, post_repo: MongoPostRepository, user_repo: MongoUserRepository, tag_repo: MongoTagRepository = None):
        self.post_repo = post_repo
        self.user_repo = user_repo
        self.tag_repo = tag_repo
        self.tag_service = TagService(tag_repo) if tag_repo else None

    async def _process_tag_inputs(self, tag_inputs: list) -> Tuple[list, list, list]:
        """
        Process TagInput objects and return tag_ids, tag_names, and tag_slugs
        Args:
            tag_inputs: List of TagInput objects with id and/or name
        Returns:
            Tuple of (tag_ids, tag_names, tag_slugs)
        """
        tag_ids = []
        tag_names = []
        tag_slugs = []
        
        if not tag_inputs or not self.tag_repo:
            return tag_ids, tag_names, tag_slugs
        
        for tag_input in tag_inputs:
            # Handle TagInput object (from DTO)
            if hasattr(tag_input, 'id') or hasattr(tag_input, 'name'):
                tag_id = getattr(tag_input, 'id', None)
                tag_name = getattr(tag_input, 'name', None)
            # Handle dict (from model_dump)
            elif isinstance(tag_input, dict):
                tag_id = tag_input.get('id')
                tag_name = tag_input.get('name')
            # Handle string (backward compatibility)
            elif isinstance(tag_input, str):
                tag_id = None
                tag_name = tag_input
            else:
                continue
            
            if tag_id:
                # If ID is provided, use it (verify it exists)
                try:
                    tag_obj = await self.tag_repo.get_by_id(tag_id)
                    if tag_obj:
                        tag_ids.append(tag_id)
                        tag_names.append(tag_obj.get("name", tag_name or ""))
                        tag_slugs.append(tag_obj.get("slug", ""))
                    elif tag_name:
                        # ID doesn't exist but name provided, create new tag
                        if self.tag_service:
                            new_tag = await self.tag_service.create_tag(
                                name=tag_name,
                                slug_str=None
                            )
                            tag_ids.append(str(new_tag["_id"]))
                            tag_names.append(tag_name)
                            tag_slugs.append(new_tag.get("slug", ""))
                except Exception:
                    # Invalid ID format, try to find or create by name
                    if tag_name and self.tag_service:
                        found_tag = await self.tag_repo.get_by_name(tag_name)
                        if found_tag:
                            tag_ids.append(str(found_tag["_id"]))
                            tag_names.append(tag_name)
                            tag_slugs.append(found_tag.get("slug", ""))
                        else:
                            new_tag = await self.tag_service.create_tag(
                                name=tag_name,
                                slug_str=None
                            )
                            tag_ids.append(str(new_tag["_id"]))
                            tag_names.append(tag_name)
                            tag_slugs.append(new_tag.get("slug", ""))
            elif tag_name:
                # Only name provided, find or create
                if self.tag_service:
                    found_tag = await self.tag_repo.get_by_name(tag_name)
                    if found_tag:
                        tag_ids.append(str(found_tag["_id"]))
                        tag_names.append(tag_name)
                        tag_slugs.append(found_tag.get("slug", ""))
                    else:
                        new_tag = await self.tag_service.create_tag(
                            name=tag_name,
                            slug_str=None
                        )
                        tag_ids.append(str(new_tag["_id"]))
                        tag_names.append(tag_name)
                        tag_slugs.append(new_tag.get("slug", ""))
        
        return tag_ids, tag_names, tag_slugs

    async def get_all_posts(self, skip: int = 0, limit: int = 10, tag_ids: list = None, tag_names: list = None, match_all: bool = True):
        """
        Get all posts with optional tag filtering
        Args:
            skip: Number of posts to skip
            limit: Maximum number of posts to return
            tag_ids: List of tag IDs to filter by
            tag_names: List of tag names to filter by
            match_all: If True, posts must have ALL tags (AND). If False, posts must have ANY tag (OR)
        """
        if tag_ids:
            # Filter by tag IDs
            tag_object_ids = [ObjectId(tid) if isinstance(tid, str) else tid for tid in tag_ids]
            posts = await self.post_repo.find_by_tag_ids(tag_object_ids, match_all=match_all, skip=skip, limit=limit)
            total = await self.post_repo.count_by_tag_ids(tag_object_ids, match_all=match_all)
        elif tag_names:
            # Filter by tag names (optimized using denormalized field)
            posts = await self.post_repo.find_by_tag_names(tag_names, match_all=match_all, skip=skip, limit=limit)
            total = await self.post_repo.count_by_tag_names(tag_names, match_all=match_all)
        else:
            # No tag filtering
            posts = await self.post_repo.list_posts(skip=skip, limit=limit)
            total = await self.post_repo.count_posts()
        return posts, total
    
    async def create_post(self, 
                          title: str, 
                          content: str, 
                          slug_str: str,  
                          excerpt: str = None, 
                          tags: list = [], 
                          category_id: str = None,
                          user_id: str = None,
                          thumbnail: str = None,
                          banner: str = None
                          ):
        # Handle tags: process TagInput objects and get their IDs, names, and slugs
        tag_ids = []
        tag_names = []
        tag_slugs = []
        if tags:
            # Check if tags are TagInput objects or simple strings (backward compatibility)
            if tags and isinstance(tags[0], (dict, type)) and (hasattr(tags[0], 'id') or hasattr(tags[0], 'name') or isinstance(tags[0], dict)):
                # New format: TagInput objects
                tag_ids, tag_names, tag_slugs = await self._process_tag_inputs(tags)
            else:
                # Old format: simple strings (backward compatibility)
                if self.tag_service:
                    tag_ids = await self.tag_service.find_or_create_tags(tags)
                    if tag_ids:
                        tag_objects = await self.tag_repo.get_by_ids(tag_ids)
                        tag_names = [tag.get("name", "") for tag in tag_objects if tag]
                        tag_slugs = [tag.get("slug", "") for tag in tag_objects if tag]
            
            # Increment usage count for each tag
            if self.tag_repo:
                for tag_id in tag_ids:
                    await self.tag_repo.increment_usage_count(tag_id)
        
        # Convert tag_ids to ObjectIds
        tag_object_ids = [ObjectId(tid) for tid in tag_ids] if tag_ids else []
        
        # Create post aggregate
        author = await self.user_repo.get_by_id(user_id)
        post = PostEntity(
            id=ObjectId(),
            slug=Slug(slug_str),
            title=title,
            content=content,
            excerpt=excerpt,
            status=PostStatus.DRAFT,
            tag_ids=tag_object_ids,
            tag_names=tag_names,  # Store tag names for faster reads
            tag_slugs=tag_slugs,  # Store tag slugs for faster reads
            category_id=ObjectId(category_id) if category_id else None,
            author_name=author.get("full_name") if author else "Unknown",
            author_email=author.get("email") if author else "Unknown",
            thumbnail=thumbnail,
            banner=banner
        )
        saved_post = await self.post_repo.create_post(post)
        return saved_post
    
    async def get_by_id(self, post_id):
        return await self.post_repo.get_by_id(post_id)
    
    async def update_post(self, post_id, post_data):
        # Get current post to track tag changes
        current_post = await self.post_repo.get_by_id(ObjectId(post_id))
        old_tag_ids = set(str(tid) for tid in current_post.get('tag_ids', [])) if current_post else set()
        
        # Convert Pydantic model to dict, excluding None values for partial updates
        update_dict = post_data.model_dump(exclude_none=True)
        
        # Handle tags if provided
        if 'tags' in update_dict:
            tag_inputs = update_dict.pop('tags', [])
            # Process TagInput objects
            new_tag_ids, new_tag_names, new_tag_slugs = await self._process_tag_inputs(tag_inputs)
            
            # Convert to ObjectIds
            update_dict['tag_ids'] = [ObjectId(tid) for tid in new_tag_ids]
            update_dict['tag_names'] = new_tag_names  # Store tag names for faster reads
            update_dict['tag_slugs'] = new_tag_slugs  # Store tag slugs for faster reads
            
            # Update usage counts
            new_tag_ids_set = set(new_tag_ids)
            # Increment for newly added tags
            for tag_id in new_tag_ids_set - old_tag_ids:
                await self.tag_repo.increment_usage_count(tag_id)
            # Decrement for removed tags
            for tag_id in old_tag_ids - new_tag_ids_set:
                await self.tag_repo.decrement_usage_count(tag_id)
        elif 'tag_ids' in update_dict:
            # If tag_ids are provided directly, convert to ObjectIds and fetch names and slugs
            tag_ids = update_dict['tag_ids']
            if tag_ids:
                tag_object_ids = [ObjectId(tid) if isinstance(tid, str) else tid for tid in tag_ids]
                update_dict['tag_ids'] = tag_object_ids
                # Fetch tag names and slugs for denormalization
                if self.tag_repo:
                    tag_ids_str = [str(tid) for tid in tag_object_ids]
                    tag_objects = await self.tag_repo.get_by_ids(tag_ids_str)
                    update_dict['tag_names'] = [tag.get("name", "") for tag in tag_objects if tag]
                    update_dict['tag_slugs'] = [tag.get("slug", "") for tag in tag_objects if tag]
        
        # Convert ObjectId string to ObjectId for category_id if present
        if 'category_id' in update_dict and update_dict['category_id']:
            update_dict['category_id'] = ObjectId(update_dict['category_id'])
        
        # Update updated_at timestamp
        from datetime import datetime, timezone
        update_dict['updated_at'] = datetime.now(timezone.utc)
        
        return await self.post_repo.update_post(ObjectId(post_id), update_dict)
    
    async def delete_post(self, post_id)-> bool: 
        return await self.post_repo.delete(post_id)
    
    async def publish_post(self, post_id: str):
        """Publish a post by setting status to PUBLISHED and setting published_at timestamp"""
        from datetime import datetime, timezone
        
        # Check if post exists
        post = await self.get_by_id(post_id)
        if not post:
            return None
        
        # Prepare update data
        update_dict = {
            'status': PostStatus.PUBLISHED.value,
            'updated_at': datetime.now(timezone.utc)
        }
        
        # Only set published_at if it's not already set (first time publishing)
        if not post.get('published_at'):
            update_dict['published_at'] = datetime.now(timezone.utc)
        
        return await self.post_repo.update_post(ObjectId(post_id), update_dict)
    
    async def unpublish_post(self, post_id: str):
        """Unpublish a post by setting status back to DRAFT"""
        from datetime import datetime, timezone
        
        # Check if post exists
        post = await self.get_by_id(post_id)
        if not post:
            return None
        
        # Prepare update data - set status to DRAFT
        update_dict = {
            'status': PostStatus.DRAFT.value,
            'updated_at': datetime.now(timezone.utc),
            'published_at': None
        }
        
        # Note: We keep published_at timestamp for historical purposes
        
        return await self.post_repo.update_post(ObjectId(post_id), update_dict)
    

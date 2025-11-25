from src.core.value_objects.slug import Slug
from src.domain.tags.entity import TagEntity
from src.infrastructure.mongo.tag_repository_impl import MongoTagRepository
from src.utils.py_object_id import PyObjectId
from bson import ObjectId


class TagService:
    def __init__(self, tag_repo: MongoTagRepository):
        self.tag_repo = tag_repo

    async def get_all_tags(self, skip: int = 0, limit: int = 10):
        tags = await self.tag_repo.list_tags(skip=skip, limit=limit)
        total = await self.tag_repo.count_tags()
        return tags, total

    async def create_tag(self, name: str, description: str = None, slug_str: str = None):
        # Generate slug from name if not provided
        if not slug_str:
            slug_str = name.lower().replace(" ", "-")
        
        # Check if tag with same slug already exists
        existing_tag = await self.tag_repo.get_by_slug(slug_str)
        if existing_tag:
            raise ValueError(f"Tag with slug '{slug_str}' already exists")

        tag_data = TagEntity(
            name=name,
            description=description,
            slug=Slug(slug_str)
        )

        saved_tag = await self.tag_repo.create_tag(tag_data)
        return saved_tag

    async def get_tag_by_id(self, tag_id: str):
        tag = await self.tag_repo.get_by_id(tag_id)
        return tag

    async def get_tag_by_slug(self, slug: str):
        tag = await self.tag_repo.get_by_slug(slug)
        return tag

    async def get_tags_by_ids(self, tag_ids: list):
        """Get multiple tags by their IDs"""
        tags = await self.tag_repo.get_by_ids(tag_ids)
        return tags

    async def find_or_create_tags(self, tag_names: list) -> list:
        """
        Find existing tags by name or create new ones.
        Returns list of tag IDs.
        """
        tag_ids = []
        for tag_name in tag_names:
            if not tag_name or not tag_name.strip():
                continue
            
            tag_name = tag_name.strip()
            # Check if tag exists by name (case-insensitive)
            existing_tag = await self.tag_repo.get_by_name(tag_name)
            
            if existing_tag:
                tag_ids.append(str(existing_tag["_id"]))
            else:
                # Create new tag
                slug_str = tag_name.lower().replace(" ", "-")
                tag_data = TagEntity(
                    name=tag_name,
                    slug=Slug(slug_str)
                )
                saved_tag = await self.tag_repo.create_tag(tag_data)
                tag_ids.append(str(saved_tag["_id"]))
        
        return tag_ids

    async def update_tag(self, tag_id: str, name: str = None, description: str = None, slug_str: str = None):
        from datetime import datetime, timezone
        update_data = {}
        
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if slug_str is not None:
            # Check if slug is already taken by another tag
            existing_tag = await self.tag_repo.get_by_slug(slug_str)
            if existing_tag and str(existing_tag["_id"]) != tag_id:
                raise ValueError(f"Tag with slug '{slug_str}' already exists")
            update_data["slug"] = str(Slug(slug_str))
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        updated_tag = await self.tag_repo.update_tag(tag_id, update_data)
        return updated_tag

    async def delete_tag(self, tag_id: str):
        deleted = await self.tag_repo.delete(tag_id)
        return deleted


from src.core.value_objects.slug import Slug
from src.domain.categories.entity import CategoryEntity
from src.infrastructure.mongo.category_repository_impl import MongoCategoryRepository
from src.utils.py_object_id import PyObjectId
from bson import ObjectId

class CategoryService:
    def __init__(self, category_repo: MongoCategoryRepository):
        self.category_repo = category_repo

    async def get_all_categories(self, skip: int = 0, limit: int = 10):
        categories = await self.category_repo.list_categories(skip=skip, limit=limit)
        total = await self.category_repo.count_categories()
        return categories,total

    async def create_category(self, name: str, description: str = None, slug_str: str = None, parent_id: str = None):


        
        category_data = CategoryEntity(
            name=name,
            description=description,
            slug=Slug(slug_str),
            parent_id= ObjectId(parent_id) if parent_id else None
        )

        saved_category = await self.category_repo.create_category(category_data)
        return saved_category
    
    async def delete_category(self, category_id: str):
        deleted = await self.category_repo.delete(category_id)
        return deleted
    async def update_category(self, category_id: str, name: str = None, description: str = None, slug_str: str = None, parent_id: str = None):
        from datetime import datetime, timezone
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if slug_str is not None:
            update_data["slug"] = str(Slug(slug_str))
        if parent_id is not None:
            update_data["parent_id"] = ObjectId(parent_id)
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        updated_category = await self.category_repo.update_category(category_id, update_data)
        return updated_category
    async def get_category_by_id(self, category_id: str):
        category = await self.category_repo.get_category_with_children(category_id)
        return category
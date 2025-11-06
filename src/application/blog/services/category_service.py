from src.domain.blog.entities.catetory_entity import CategoryEntity
from src.domain.blog.value_objects.slug import Slug
from src.infrastructure.mongo.repositories.mongo_category_repo import MongoCategoryRepository
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

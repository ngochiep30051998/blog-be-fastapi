from abc import ABC, abstractmethod

class CategoryRepository(ABC):
    @abstractmethod
    async def create_category(self, category_data):
        pass

    @abstractmethod
    async def get_by_id(self, category_id):
        pass

    @abstractmethod
    async def update_category(self, category_id, category_data):
        pass

    @abstractmethod
    async def delete(self, id):
        pass

    @abstractmethod
    async def list_categories(self, skip: int = 0, limit: int = 10):
        pass
from abc import ABC, abstractmethod

class TagRepository(ABC):
    @abstractmethod
    async def create_tag(self, tag_data):
        pass

    @abstractmethod
    async def get_by_id(self, tag_id):
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str):
        pass

    @abstractmethod
    async def get_by_name(self, name: str):
        pass

    @abstractmethod
    async def get_by_ids(self, tag_ids: list):
        pass

    @abstractmethod
    async def update_tag(self, tag_id, tag_data):
        pass

    @abstractmethod
    async def delete(self, id):
        pass

    @abstractmethod
    async def list_tags(self, skip: int = 0, limit: int = 10):
        pass

    @abstractmethod
    async def increment_usage_count(self, tag_id):
        pass

    @abstractmethod
    async def decrement_usage_count(self, tag_id):
        pass


from abc import ABC, abstractmethod

class PostRepository(ABC):
    @abstractmethod
    async def create_post(self, post_data):
        pass

    @abstractmethod
    async def get_by_id(self, post_id):
        pass

    @abstractmethod
    async def update_post(self, post_id, post_data):
        pass

    @abstractmethod
    async def delete(self, id):
        pass

    @abstractmethod
    async def list_posts(self, skip: int = 0, limit: int = 10):
        pass
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def create_user(self, user_data):
        pass

    @abstractmethod
    async def get_by_id(self, user_id):
        pass

    @abstractmethod
    async def update_user(self, user_id, user_data):
        pass

    @abstractmethod
    async def delete(self, id):
        pass

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 10):
        pass
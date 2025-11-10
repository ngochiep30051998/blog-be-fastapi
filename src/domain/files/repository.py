from abc import ABC, abstractmethod

class FileRepository(ABC):
    @abstractmethod
    async def create_file(self, file_data):
        pass

    @abstractmethod
    async def get_by_id(self, file_id):
        pass

    @abstractmethod
    async def update_file(self, file_id, file_data):
        pass

    @abstractmethod
    async def delete(self, file_id):
        pass

    @abstractmethod
    async def list_files(self, skip: int = 0, limit: int = 10):
        pass
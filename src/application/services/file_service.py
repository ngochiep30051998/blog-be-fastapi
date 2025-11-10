from src.infrastructure.mongo.file_repository_impl import MongoFileRepository


class FileService:
    def __init__(self, repository: MongoFileRepository):
        self.repository = repository

    async def create_file(self, file_data):
        return await self.repository.create_file(file_data)

    async def get_file(self, file_id):
        return await self.repository.get_by_id(file_id)

    async def update_file(self, file_id, file_data):
        await self.repository.update_file(file_id, file_data)

    async def delete_file(self, file_id):
        await self.repository.delete(file_id)

    async def list_files(self, skip: int = 0, limit: int = 10):
        files = await self.repository.list_files(skip, limit)
        total = await self.repository.count_files()
        return files, total
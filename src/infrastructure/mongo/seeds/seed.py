from bson import ObjectId
from typing import List

from src.application.services.user_service import UserService
from src.config import settings
from src.domain.users.entity import UserEntity
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from src.infrastructure.mongo.database import get_database

class MongoSeeder:
    def __init__(self, service: UserService):
        self.service = service

    async def seed_users(self, users: List[dict]):
        for user in users:
            existing = await self.service.get_by_email(user["email"])
            if not existing:

                await self.service.register_user(email=user["email"],
                                                  full_name=user["username"],
                                                  password=user["password"],
                                                  role=user["role"], date_of_birth=user["date_of_birth"])

    async def run(self):
        users = [
            {
                "username": settings.DEFAULT_USER_FULL_NAME,
                "email": settings.DEFAULT_USER_EMAIL,
                "password": settings.DEFAULT_USER_PASSWORD,
                "role": settings.DEFAULT_USER_ROLE,
                "date_of_birth": settings.DEFAULT_USER_DATE_OF_BIRTH
            }
        ]

        await self.seed_users(users)
        print("Seed users completed")

# Hàm chạy seed (thường gọi trong event startup)
async def seed_db():
    db = get_database()
    user_repo = MongoUserRepository(db)
    user_service = UserService(user_repo)
    seeder = MongoSeeder(user_service)
    await seeder.run()

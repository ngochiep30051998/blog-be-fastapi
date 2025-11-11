# src/config/settings.py

from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""
    MONGODB_URL: str
    MONGO_ROOT_USERNAME: str 
    MONGO_ROOT_PASSWORD: str
    MONGODB_DB_NAME: str
    API_V1_PREFIX: str
    LOG_LEVEL: str
    DEBUG: bool
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    APP_PORT: int = 8000
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PUBLIC_ROUTES: List[str] = []
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_CLOUD_FOLDER: str
    ALLOWED_MIME_TYPES: str = {"image/jpeg", "image/png", "image/gif"}
    DEFAULT_USER_EMAIL: str
    DEFAULT_USER_PASSWORD: str
    DEFAULT_USER_FULL_NAME: str
    DEFAULT_USER_ROLE: str
    DEFAULT_USER_DATE_OF_BIRTH: str
    ENABLE_SEED_DATA: Optional[bool] = False
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None
    ENABLE_RATE_LIMITING: Optional[bool] = True
    class Config:
        env_file = ".env"

settings = Settings()
# src/config/settings.py

from pydantic_settings import BaseSettings
from typing import List

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
    PUBLIC_ROUTES: List[str] = [
        "/",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health"
    ]
    class Config:
        env_file = ".env"

settings = Settings()
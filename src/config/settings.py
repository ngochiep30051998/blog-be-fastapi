# src/config/settings.py

from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import List, Optional, Set, Union, Any, Dict

class Settings(BaseSettings):
    """Application settings"""
    MONGODB_URL: str
    MONGO_ROOT_USERNAME: str 
    MONGO_ROOT_PASSWORD: str
    MONGODB_DB_NAME: str
    API_V1_PREFIX: str
    LOG_LEVEL: str
    DEBUG: bool
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080","http://localhost:4200"]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if v is None:
            return ["http://localhost:3000", "http://localhost:8080", "http://localhost:4200"]
        if isinstance(v, str):
            # Split by comma and strip whitespace
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:8080", "http://localhost:4200"]
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        if isinstance(v, list):
            return v
        return v
    
    @field_validator('PUBLIC_ROUTES', mode='before')
    @classmethod
    def parse_public_routes(cls, v: Union[str, List[str], None]) -> List[str]:
        """Parse PUBLIC_ROUTES from comma-separated string or list"""
        if v is None:
            return []
        if isinstance(v, str):
            # Split by comma and strip whitespace, or return empty list if empty string
            if not v.strip():
                return []
            return [route.strip() for route in v.split(',') if route.strip()]
        if isinstance(v, list):
            return v
        return v
    
    APP_PORT: int = 8000
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PUBLIC_ROUTES: List[str] = []
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_CLOUD_FOLDER: str
    ALLOWED_MIME_TYPES_STR: str = "image/jpeg,image/png,image/gif"
    
    @model_validator(mode='before')
    @classmethod
    def handle_allowed_mime_types_alias(cls, data: Any) -> Any:
        """Handle both ALLOWED_MIME_TYPES and ALLOWED_MIME_TYPES_STR environment variables"""
        if isinstance(data, dict):
            # If ALLOWED_MIME_TYPES is present but ALLOWED_MIME_TYPES_STR is not, copy it
            if 'ALLOWED_MIME_TYPES' in data and 'ALLOWED_MIME_TYPES_STR' not in data:
                data['ALLOWED_MIME_TYPES_STR'] = data['ALLOWED_MIME_TYPES']
            # Remove ALLOWED_MIME_TYPES to avoid "extra inputs" error
            data.pop('ALLOWED_MIME_TYPES', None)
        return data
    
    @property
    def ALLOWED_MIME_TYPES(self) -> Set[str]:
        """Parse ALLOWED_MIME_TYPES_STR into a set"""
        if not self.ALLOWED_MIME_TYPES_STR or not self.ALLOWED_MIME_TYPES_STR.strip():
            return {"image/jpeg", "image/png", "image/gif"}
        return {mime.strip() for mime in self.ALLOWED_MIME_TYPES_STR.split(',') if mime.strip()}
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
    ENVIRONMENT: Optional[str] = None  # Added environment setting
    MAX_FAILED_LOGIN_ATTEMPTS: Optional[int] = 5  # Maximum failed login attempts before lockout
    ACCOUNT_LOCKOUT_DURATION_MINUTES: Optional[int] = 15  # Account lockout duration in minutes (15-30)
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from environment to avoid errors

settings = Settings()
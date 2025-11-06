from datetime import datetime, timedelta, timezone
import email
import hashlib
from typing import Optional

from bson import ObjectId
from src.config import settings
from src.core.role import UserRole
from src.domain.users.entity import UserEntity
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
import bcrypt
import jwt

class UserService:
    def __init__(self, user_repo: MongoUserRepository):
        self.user_repo = user_repo
        
    def hash_password(self, plain_password: str) -> str:
        # First convert to SHA256 to handle long passwords and ensure consistent length
        sha256_pass = hashlib.sha256(plain_password.encode()).hexdigest()
        # Then hash with bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(sha256_pass.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # Convert to SHA256 first (same as in hash_password)
        sha256_pass = hashlib.sha256(plain_password.encode()).hexdigest()
        # Verify with bcrypt
        return bcrypt.checkpw(sha256_pass.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str):
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False
        if not self.verify_password(password, user.get('password_hash')):
            return False
        return user
    
    async def register_user(self, full_name: str, email: str, password: str, date_of_birth=None):
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")
        hashed_password = self.hash_password(password)
        new_user = UserEntity(
            id=ObjectId(),
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role=UserRole.USER,
            date_of_birth=date_of_birth,
        )
        saved_user = await self.user_repo.create_user(new_user)

        access_token = self.create_access_token(data={"sub": str(saved_user["_id"])})

        return access_token
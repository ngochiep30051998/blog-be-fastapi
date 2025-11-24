from datetime import datetime, timedelta, timezone
import email
import hashlib
from typing import Optional

from bson import ObjectId
from src.config import settings
from src.core.role import UserRole
from src.domain.users.entity import UserEntity
from src.infrastructure.mongo.user_repository_impl import MongoUserRepository
from src.application.services.session_service import SessionService
import bcrypt
import jwt

class UserService:
    def __init__(self, user_repo: MongoUserRepository, session_service: Optional[SessionService] = None):
        self.user_repo = user_repo
        self.session_service = session_service or SessionService()
        
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
        print(" to_encode:", to_encode)
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str):
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False
        if not self.verify_password(password, user.get('password_hash')):
            return False
        return user
    
    async def register_user(self, full_name: str, email: str, password: str, date_of_birth=None, role: UserRole = None):
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")
        hashed_password = self.hash_password(password)
        new_user = UserEntity(
            id=ObjectId(),
            full_name=full_name,
            email=email,
            password_hash=hashed_password,
            role=role or UserRole.GUEST,
            date_of_birth=datetime.strptime(date_of_birth, "%Y-%m-%d"),
        )
        saved_user = await self.user_repo.create_user(new_user)

        access_token = self.create_access_token(data={"sub": str(saved_user["_id"]), "role": saved_user["role"]})
        
        # Store session in Redis (this will invalidate any existing session)
        user_id = str(saved_user["_id"])
        expires_in_seconds = self.session_service.get_token_expiration_seconds(access_token)
        await self.session_service.store_session(user_id, access_token, expires_in_seconds)

        return access_token
    
    async def login_user(self, email: str, password: str) -> Optional[str]:
        """
        Authenticate user and create a new session token.
        This will invalidate any existing session for the user.
        
        Returns:
            JWT token if authentication succeeds, None otherwise
        
        Raises:
            ValueError: If user is locked
        """
        user = await self.authenticate_user(email, password)
        if not user:
            return None
        
        # Check if user is locked
        if user.get("locked", False):
            raise ValueError("User account is locked. Please contact an administrator.")
        
        user_id = str(user["_id"])
        # Invalidate any existing session before creating new one
        await self.session_service.invalidate_session(user_id)
        
        # Create new token
        access_token = self.create_access_token(data={"sub": user_id, "role": user["role"]})
        
        # Store session in Redis
        expires_in_seconds = self.session_service.get_token_expiration_seconds(access_token)
        await self.session_service.store_session(user_id, access_token, expires_in_seconds)
        
        return access_token
    
    async def get_by_id(self, user_id: str):
        user =  await self.user_repo.get_by_id(user_id)
        return user
    async def get_by_email(self, email: str):
        user = await self.user_repo.get_by_email(email)
        return user
    
    async def list_users(self, skip: int = 0, limit: int = 10):
        """List all users (excluding password_hash)"""
        users = await self.user_repo.list_users(skip, limit)
        return users
    
    async def update_user(self, user_id: str, update_data: dict):
        """Update user information"""
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        if not update_data:
            raise ValueError("No fields to update")
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update user and get updated user (password_hash already removed by repository)
        updated_user = await self.user_repo.update_user(ObjectId(user_id), update_data)
        if not updated_user:
            raise ValueError("User not found or update failed")
        return updated_user
    
    async def lock_user(self, user_id: str, locked: bool):
        """Lock or unlock a user"""
        update_data = {
            "locked": locked,
            "updated_at": datetime.now(timezone.utc)
        }
        # Update user and get updated user (password_hash already removed by repository)
        updated_user = await self.user_repo.update_user(ObjectId(user_id), update_data)
        if not updated_user:
            raise ValueError("User not found or update failed")
        return updated_user
    
    async def change_password(self, user_id: str, old_password: str, new_password: str):
        """
        Change user password
        Verifies old password before setting new password
        
        Raises:
            ValueError: If user not found, old password is incorrect, or user is locked
        """
        # Get user with password_hash
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if user is locked
        if user.get("locked", False):
            raise ValueError("User account is locked. Please contact an administrator.")
        
        # Verify old password
        if not self.verify_password(old_password, user.get('password_hash')):
            raise ValueError("Old password is incorrect")
        
        # Hash new password
        new_password_hash = self.hash_password(new_password)
        
        # Update password
        update_data = {
            "password_hash": new_password_hash,
            "updated_at": datetime.now(timezone.utc)
        }
        
        updated_user = await self.user_repo.update_user(ObjectId(user_id), update_data)
        if not updated_user:
            raise ValueError("Failed to update password")
        
        # Invalidate all existing sessions for security (force re-login)
        await self.session_service.invalidate_session(user_id)
        
        return updated_user
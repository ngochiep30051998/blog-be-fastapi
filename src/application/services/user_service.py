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
    
    def _is_account_locked(self, user: dict) -> bool:
        """Check if account is locked (either manually locked or lockout period active)"""
        if user.get("locked", False):
            return True
        
        # Check if lockout period has expired
        locked_until = user.get("locked_until")
        if locked_until:
            # Handle both datetime objects and ISO format strings
            if isinstance(locked_until, str):
                try:
                    locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    # Fallback: try parsing common formats
                    try:
                        locked_until = datetime.strptime(locked_until, "%Y-%m-%dT%H:%M:%S.%fZ")
                        locked_until = locked_until.replace(tzinfo=timezone.utc)
                    except ValueError:
                        # If parsing fails, assume not locked
                        return False
            # Ensure timezone awareness
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            
            if locked_until > datetime.now(timezone.utc):
                return True
            else:
                # Lockout period expired, but account might still be marked as locked
                # We'll auto-unlock it
                return False
        
        return False
    
    async def _increment_failed_attempts(self, user_id: str) -> dict:
        """Increment failed login attempts and lock account if threshold reached"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        failed_attempts = user.get("failed_attempts", 0) + 1
        max_attempts = settings.MAX_FAILED_LOGIN_ATTEMPTS or 5
        
        update_data = {
            "failed_attempts": failed_attempts,
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Lock account if threshold reached
        if failed_attempts >= max_attempts:
            lockout_duration = settings.ACCOUNT_LOCKOUT_DURATION_MINUTES or 15
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_duration)
            update_data["locked"] = True
            update_data["locked_until"] = locked_until
        
        updated_user = await self.user_repo.update_user(ObjectId(user_id), update_data)
        return updated_user
    
    async def _reset_failed_attempts(self, user_id: str):
        """Reset failed login attempts on successful login"""
        update_data = {
            "failed_attempts": 0,
            "updated_at": datetime.now(timezone.utc)
        }
        await self.user_repo.update_user(ObjectId(user_id), update_data)
    
    async def authenticate_user(self, email: str, password: str):
        """Authenticate user and check lockout status"""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False
        
        # Check if account is locked BEFORE password verification
        if self._is_account_locked(user):
            # If lockout period expired, auto-unlock
            locked_until = user.get("locked_until")
            if locked_until:
                # Handle both datetime objects and ISO format strings
                if isinstance(locked_until, str):
                    try:
                        locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        try:
                            locked_until = datetime.strptime(locked_until, "%Y-%m-%dT%H:%M:%S.%fZ")
                            locked_until = locked_until.replace(tzinfo=timezone.utc)
                        except ValueError:
                            # If parsing fails, treat as expired
                            locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
                
                # Ensure timezone awareness
                if locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                
                if locked_until <= datetime.now(timezone.utc):
                    # Auto-unlock expired lockout
                    await self.user_repo.update_user(
                        ObjectId(str(user["_id"])),
                        {
                            "locked": False,
                            "locked_until": None,
                            "failed_attempts": 0,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    )
                    # Re-fetch user after unlock
                    user = await self.user_repo.get_by_email(email)
                else:
                    # Still locked
                    remaining_minutes = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
                    raise ValueError(f"User account is locked. Please try again in {remaining_minutes} minutes or contact an administrator.")
            else:
                # Manually locked
                raise ValueError("User account is locked. Please contact an administrator.")
        
        # Verify password
        if not self.verify_password(password, user.get('password_hash')):
            # Increment failed attempts
            await self._increment_failed_attempts(str(user["_id"]))
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
            ValueError: If user is locked or account is locked
        """
        try:
            user = await self.authenticate_user(email, password)
        except ValueError as e:
            # Re-raise lockout errors
            raise e
        
        if not user:
            return None
        
        user_id = str(user["_id"])
        
        # Reset failed attempts on successful login
        await self._reset_failed_attempts(user_id)
        
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
        # If unlocking, also clear lockout-related fields
        if not locked:
            update_data["locked_until"] = None
            update_data["failed_attempts"] = 0
        # Update user and get updated user (password_hash already removed by repository)
        updated_user = await self.user_repo.update_user(ObjectId(user_id), update_data)
        if not updated_user:
            raise ValueError("User not found or update failed")
        return updated_user
    
    async def unlock_user(self, user_id: str):
        """
        Unlock a user account (admin only).
        Resets all lockout-related fields: locked, failed_attempts, locked_until
        """
        update_data = {
            "locked": False,
            "locked_until": None,
            "failed_attempts": 0,
            "updated_at": datetime.now(timezone.utc)
        }
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
        
        # Check if user is locked (using same logic as login)
        if self._is_account_locked(user):
            # Check if lockout period expired
            locked_until = user.get("locked_until")
            if locked_until:
                if isinstance(locked_until, str):
                    try:
                        locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        try:
                            locked_until = datetime.strptime(locked_until, "%Y-%m-%dT%H:%M:%S.%fZ")
                            locked_until = locked_until.replace(tzinfo=timezone.utc)
                        except ValueError:
                            locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
                if locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                
                if locked_until > datetime.now(timezone.utc):
                    remaining_minutes = int((locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
                    raise ValueError(f"User account is locked. Please try again in {remaining_minutes} minutes or contact an administrator.")
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
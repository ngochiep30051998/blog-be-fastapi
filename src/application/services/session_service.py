from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

from src.config import settings
from src.infrastructure.cache.redis import redis_client


class SessionService:
    """Service for managing user sessions in Redis"""
    
    def __init__(self):
        self.redis = redis_client
        self.session_prefix = "session:"
        self.token_prefix = "token:"
    
    def _get_session_key(self, user_id: str) -> str:
        """Get Redis key for user session"""
        return f"{self.session_prefix}{user_id}"
    
    def _get_token_key(self, token: str) -> str:
        """Get Redis key for token lookup"""
        # Use a hash of the token to avoid storing full token as key
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"{self.token_prefix}{token_hash}"
    
    async def store_session(self, user_id: str, token: str, expires_in_seconds: int) -> None:
        """
        Store a new session token for a user.
        This will invalidate any existing session for the user.
        
        Args:
            user_id: User ID
            token: JWT token
            expires_in_seconds: Token expiration time in seconds
        """
        session_key = self._get_session_key(user_id)
        token_key = self._get_token_key(token)
        
        # Get existing token for this user (if any) to invalidate it
        existing_token = await self.redis.get(session_key)
        if existing_token:
            existing_token_str = existing_token.decode('utf-8')
            existing_token_key = self._get_token_key(existing_token_str)
            # Delete the old token mapping
            await self.redis.delete(existing_token_key)
        
        # Store new session: user_id -> token
        await self.redis.setex(
            session_key,
            expires_in_seconds,
            token
        )
        
        # Store reverse mapping: token_hash -> user_id (for quick lookup)
        await self.redis.setex(
            token_key,
            expires_in_seconds,
            user_id
        )
    
    async def is_token_valid(self, token: str) -> bool:
        """
        Check if a token is valid (exists in Redis)
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is valid, False otherwise
        """
        token_key = self._get_token_key(token)
        exists = await self.redis.exists(token_key)
        return bool(exists)
    
    async def invalidate_session(self, user_id: str) -> None:
        """
        Invalidate a user's session by removing it from Redis
        
        Args:
            user_id: User ID whose session should be invalidated
        """
        session_key = self._get_session_key(user_id)
        existing_token = await self.redis.get(session_key)
        
        if existing_token:
            existing_token_str = existing_token.decode('utf-8')
            token_key = self._get_token_key(existing_token_str)
            # Delete both mappings
            await self.redis.delete(session_key)
            await self.redis.delete(token_key)
    
    async def invalidate_token(self, token: str) -> None:
        """
        Invalidate a specific token
        
        Args:
            token: JWT token to invalidate
        """
        token_key = self._get_token_key(token)
        user_id = await self.redis.get(token_key)
        
        if user_id:
            user_id_str = user_id.decode('utf-8')
            session_key = self._get_session_key(user_id_str)
            # Delete both mappings
            await self.redis.delete(session_key)
            await self.redis.delete(token_key)
    
    async def get_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Get user ID from token if token is valid
        
        Args:
            token: JWT token
            
        Returns:
            User ID if token is valid, None otherwise
        """
        token_key = self._get_token_key(token)
        user_id = await self.redis.get(token_key)
        if user_id:
            return user_id.decode('utf-8')
        return None
    
    def get_token_expiration_seconds(self, token: str) -> int:
        """
        Extract expiration time from JWT token and return seconds until expiration
        
        Args:
            token: JWT token
            
        Returns:
            Seconds until token expiration
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            exp = payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = exp_datetime - now
                return max(int(delta.total_seconds()), 0)
            return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        except Exception:
            # If token parsing fails, use default expiration
            return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


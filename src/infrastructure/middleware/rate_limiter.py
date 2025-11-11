import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis.asyncio import Redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AsyncRedisRateLimiter(BaseHTTPMiddleware):
    """
    Custom Redis rate limiter middleware that properly handles async operations
    """
    
    def __init__(
        self,
        app,
        redis_client: Redis,
        limit: int = 60,
        window: int = 60,
        key_func: Optional[callable] = None
    ):
        super().__init__(app)
        self.redis = redis_client
        self.limit = limit
        self.window = window
        self.key_func = key_func or self._default_key_func
    
    def _default_key_func(self, request: Request) -> str:
        """Default key function uses client IP"""
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:{client_ip}"
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and apply rate limiting"""
        try:
            # Test Redis connection first
            await self.redis.ping()
            
            # Get the rate limit key
            key = self.key_func(request)
            current_time = int(time.time())
            window_start = current_time - self.window
            
            # Use Redis pipeline for atomic operations
            async with self.redis.pipeline() as pipe:
                # Remove old entries outside the window
                await pipe.zremrangebyscore(key, 0, window_start)
                # Count current requests in window
                await pipe.zcard(key)
                # Add current request
                await pipe.zadd(key, {str(current_time): current_time})
                # Set expiration
                await pipe.expire(key, self.window)
                
                results = await pipe.execute()
                request_count = results[1]  # zcard result
            
            # Check if limit exceeded
            if request_count >= self.limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": f"Too many requests. Limit: {self.limit} per {self.window} seconds"
                    }
                )
            
            # Continue with the request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(self.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - request_count - 1))
            response.headers["X-RateLimit-Reset"] = str(current_time + self.window)
            
            return response
            
        except Exception as e:
            logger.warning(f"Rate limiter disabled due to Redis error: {e}")
            # On Redis error, allow the request to proceed without rate limiting
            response = await call_next(request)
            response.headers["X-RateLimit-Status"] = "disabled"
            return response
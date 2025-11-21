from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.infrastructure.middleware.cors_utils import add_cors_headers


class CORSMiddlewareWrapper(BaseHTTPMiddleware):
    """Middleware to add CORS headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        response = await call_next(request)
        
        # Add CORS headers to the response
        return add_cors_headers(response, request)


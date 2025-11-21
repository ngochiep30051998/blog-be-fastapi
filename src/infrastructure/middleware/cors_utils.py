from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from src.config import settings


def add_cors_headers(response: Response, request: Request) -> Response:
    """Add CORS headers to response based on request origin"""
    origin = request.headers.get("origin")
    
    # If origin is in allowed origins, use it
    if origin and origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    # If "*" is explicitly in allowed origins (for development)
    elif "*" in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = "*"
    # If no allowed origins configured and we have an origin, allow it (fallback for development)
    elif not settings.ALLOWED_ORIGINS and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    # Always set these headers (even if origin doesn't match - browser will handle rejection)
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With"
    response.headers["Access-Control-Expose-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response


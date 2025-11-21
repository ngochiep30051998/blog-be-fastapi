# src/main.py
import uvicorn
import traceback

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.config import settings
from src.infrastructure.middleware.auth_middleware import AuthMiddleware
from src.infrastructure.mongo.database import MongoDatabase
from src.domain.posts import api as postApi
from src.domain.categories import api as categoriesApi
from src.domain.auth import api as authApi
from src.domain.users import api as usersApi
from src.domain.files import api as fileApi
from fastapi.openapi.utils import get_openapi

from src.infrastructure.mongo.seeds.seed import seed_db
from src.infrastructure.middleware.rate_limiter import AsyncRedisRateLimiter
from src.infrastructure.cache.redis import redis_client
from src.infrastructure.middleware.cors_middleware import CORSMiddlewareWrapper
from src.infrastructure.middleware.cors_utils import add_cors_headers

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    await MongoDatabase.connect_to_mongo()
    await seed_db()
    yield
    # Shutdown
    await MongoDatabase.close_mongo_connection()

app = FastAPI(
    title="Personal Blog API",
    description="A clean DDD-based blog API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - FastAPI's built-in middleware for preflight OPTIONS requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom CORS middleware to add CORS headers to all responses
app.add_middleware(CORSMiddlewareWrapper)

# Add rate limiting middleware only if enabled
if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(
        AsyncRedisRateLimiter,
        redis_client=redis_client,
        limit=40,      # max 40 requests
        window=60      # per 60 seconds
    )
# Custom OpenAPI schema to show button Authorize
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Blog API",
        version="1.0.0",
        description="API with JWT Bearer Authentication",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token (without 'Bearer' prefix)"
        }
    }

    public_paths = settings.PUBLIC_ROUTES
    
    for path, path_item in openapi_schema["paths"].items():
        if path in public_paths:
            continue
        
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                operation["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# apply custom OpenAPI
app.openapi = custom_openapi

# Global exception handlers
# These handlers add CORS headers to error responses to prevent browser status code 0
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with CORS headers"""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    return add_cors_headers(response, request)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )
    return add_cors_headers(response, request)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers"""
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
    return add_cors_headers(response, request)

app.add_middleware(AuthMiddleware)  
# Routes
app.include_router(postApi.router)
app.include_router(categoriesApi.router)
app.include_router(authApi.router)
app.include_router(usersApi.router)
app.include_router(fileApi.router)

@app.get("/", tags=["health"])
async def root():
    return {"message": "Personal Blog API - DDD Architecture"}

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
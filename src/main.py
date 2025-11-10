# src/main.py
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.infrastructure.middleware.auth_middleware import AuthMiddleware
from src.infrastructure.mongo.database import MongoDatabase
from src.domain.posts import api as postApi
from src.domain.categories import api as categoriesApi
from src.domain.auth import api as authApi
from src.domain.users import api as usersApi
from src.domain.files import api as fileApi
from fastapi.openapi.utils import get_openapi

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    await MongoDatabase.connect_to_mongo()
    yield
    # Shutdown
    await MongoDatabase.close_mongo_connection()

app = FastAPI(
    title="Personal Blog API",
    description="A clean DDD-based blog API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# src/main.py
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.infrastructure.mongo.database import MongoDatabase
from src.domain.posts import api as postApi
from src.domain.categories import api as categoriesApi
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

# Routes
app.include_router(postApi.router)
app.include_router(categoriesApi.router)

@app.get("/", tags=["health"])
async def root():
    return {"message": "Personal Blog API - DDD Architecture"}

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
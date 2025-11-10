from typing import List
from fastapi import APIRouter, Query, Request, UploadFile
from fastapi.params import Depends

from src.application.dto.base_dto import BaseResponse
from src.application.dto.file_dto import FileResponse
from src.application.services.file_service import FileService
from src.config import settings
from src.infrastructure.mongo.database import get_database
from src.infrastructure.mongo.file_repository_impl import MongoFileRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
import cloudinary
import cloudinary.uploader
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)
router = APIRouter(prefix="/api/v1/file", tags=["file"])
async def get_file_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> FileService:
    file_repo = MongoFileRepository(db)
    return FileService(repository=file_repo)

@router.post("/upload", summary="upload file")
async def upload_file(
    image: UploadFile,
    request: Request, 
    file_service: FileService = Depends(get_file_service)):
    upload_result = cloudinary.uploader.upload(image.file)
    file_url = upload_result['secure_url']
    name = image.filename
    mine_type = upload_result['resource_type'] + '/' + upload_result['format']
    cloudinary_id = upload_result['public_id']
    user_id = request.state.user_id
    upload = await file_service.create_file(
        {"cloudinary_url": file_url, "name": name, "mime_type": mine_type, "cloudinary_id": cloudinary_id, "uploaded_by": user_id}
    )
    return BaseResponse(success=True, data={"cloudinary_url": file_url, "name": name, "mime_type": mine_type, "cloudinary_id": cloudinary_id, "_id":upload})
@router.delete("/delete/{file_id}", summary="delete file by id")
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    await file_service.delete_file(file_id)
    return BaseResponse(success=True, data={"message": "File deleted successfully"})
@router.get("/list", summary="list files", response_model=BaseResponse[List[FileResponse]])
async def list_files(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of files per page"),
    file_service: FileService = Depends(get_file_service)
):
    skip = (page - 1) * page_size
    files,total = await file_service.list_files(skip=skip, limit=page_size)
    return BaseResponse(success=True, data=files, total=total, page=page, page_size=page_size)
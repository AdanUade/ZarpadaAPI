from fastapi import APIRouter, UploadFile, File
from backend.utils.cloudinary_helper import upload_image_to_cloudinary

router = APIRouter()

@router.post("/test-cloudinary")
async def test_cloudinary(file: UploadFile = File(...)):
    url = upload_image_to_cloudinary(file.file)
    return {"url": url}
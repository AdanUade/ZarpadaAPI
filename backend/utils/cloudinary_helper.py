import cloudinary
import cloudinary.uploader
import os
from fastapi import UploadFile

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

async def upload_image_to_cloudinary(file: UploadFile, folder: str = "default"):
    try:
        result = cloudinary.uploader.upload(file.file, folder=folder)
        return result["secure_url"], result["public_id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {e}")

async def delete_image_cloudinary(public_id: str):
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Error eliminando imagen: {e}")

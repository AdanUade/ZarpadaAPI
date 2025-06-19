import cloudinary
import cloudinary.uploader
from io import BytesIO

import os
from fastapi import UploadFile

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

async def upload_image_to_cloudinary(file_or_bytes, folder="default"):
    try:
        # Si es UploadFile, extraigo el .file
        if isinstance(file_or_bytes, UploadFile):
            file_to_upload = file_or_bytes.file
        # Si es BytesIO, me quedo con el buffer directamente
        elif isinstance(file_or_bytes, BytesIO):
            file_to_upload = file_or_bytes
        # Si es bytes, lo convierto a BytesIO
        elif isinstance(file_or_bytes, bytes):
            file_to_upload = BytesIO(file_or_bytes)
        else:
            raise ValueError("Tipo de archivo no soportado")

        # Sube a Cloudinary
        result = cloudinary.uploader.upload(file_to_upload, folder=folder)
        url = result["secure_url"]
        public_id = result["public_id"]
        return url, public_id

    except Exception as e:
        raise Exception(f"Error subiendo imagen a Cloudinary: {e}")
    
async def delete_image_cloudinary(public_id: str):
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Error eliminando imagen: {e}")

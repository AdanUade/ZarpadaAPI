import cloudinary
import cloudinary.uploader
from PIL import Image
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
    """
    Acepta UploadFile, bytes o BytesIO, convierte a JPEG y lo sube a Cloudinary.
    Devuelve (secure_url, public_id).
    """
    # 1) Extraer bytes raw
    if hasattr(file_or_bytes, "file"):
        raw = file_or_bytes.file.read()
    elif isinstance(file_or_bytes, BytesIO):
        file_or_bytes.seek(0)
        raw = file_or_bytes.read()
    elif isinstance(file_or_bytes, (bytes, bytearray)):
        raw = file_or_bytes
    else:
        raise ValueError("Tipo de archivo no soportado")

    # 2) Convertir a JPEG con PIL
    try:
        img = Image.open(BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Error al decodificar imagen: {e}")

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)

    # 3) Subir el JPEG a Cloudinary
    result = cloudinary.uploader.upload(
        buf,
        folder=folder,
        format="jpg",        # fuerza extensión .jpg
        overwrite=True,
    )

    return result["secure_url"], result["public_id"]
    
async def delete_image_cloudinary(public_id: str):
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Error eliminando imagen: {e}")

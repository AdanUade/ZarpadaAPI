import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

async def upload_image_to_cloudinary(file: UploadFile, folder: str = "default"):
    try:
        # DEBUG: chequea tipo de archivo y tamaño
        print("Filename:", file.filename)
        print("Content type:", file.content_type)
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)
        print("File size:", size)
        
        result = cloudinary.uploader.upload(file.file, folder=folder)
        print("Upload result:", result)
        return result["secure_url"]
    except Exception as e:
        print("Cloudinary upload failed:", e)
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {e}")


def delete_image_from_cloudinary(public_id):
    """
    Borra una imagen de Cloudinary por su public_id.
    :param public_id: El ID público que te devuelve Cloudinary (NO la URL)
    :return: respuesta de Cloudinary
    """
    return cloudinary.uploader.destroy(public_id)

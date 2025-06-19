import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

async def upload_image_to_cloudinary(file, folder="uploads"):
    """
    Sube una imagen a Cloudinary y retorna la URL segura.
    :param file: UploadFile de FastAPI
    :param folder: Carpeta en Cloudinary
    :return: URL segura de la imagen subida
    """
    result = cloudinary.uploader.upload(file.file, folder=folder)
    return result["secure_url"]

def delete_image_from_cloudinary(public_id):
    """
    Borra una imagen de Cloudinary por su public_id.
    :param public_id: El ID público que te devuelve Cloudinary (NO la URL)
    :return: respuesta de Cloudinary
    """
    return cloudinary.uploader.destroy(public_id)

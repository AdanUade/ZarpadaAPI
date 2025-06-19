import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
  cloud_name = os.environ["CLOUDINARY_CLOUD_NAME"],
  api_key = os.environ["CLOUDINARY_API_KEY"],
  api_secret = os.environ["CLOUDINARY_API_SECRET"]
)

def upload_image_to_cloudinary(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]

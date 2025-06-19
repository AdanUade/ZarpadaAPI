import os
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
    api_key=os.environ["CLOUDINARY_API_KEY"],
    api_secret=os.environ["CLOUDINARY_API_SECRET"]
)

def upload_image_to_cloudinary(file):
    res = cloudinary.uploader.upload(file, folder="zarpado")  # podés cambiar el folder
    return res["secure_url"]

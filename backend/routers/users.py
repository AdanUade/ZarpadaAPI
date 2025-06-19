from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.db.mongo import db
from backend.models.user import UserCreate, UserOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/usuarios", response_model=UserOut)
def crear_usuario(user: UserCreate):
    user_dict = user.dict()
    user_dict["profile_image_path"] = None
    user_dict["historial"] = []
    user_dict["favoritos"] = []
    res = db["usuarios"].insert_one(user_dict)
    user_out = {**user_dict, "id": str(res.inserted_id)}
    return user_out

@router.post("/usuarios/{user_id}/profile_image")
def subir_profile_image(user_id: str, file: UploadFile = File(...)):
    url = upload_image_to_cloudinary(file.file)
    db["usuarios"].update_one({"_id": ObjectId(user_id)}, {"$set": {"profile_image_path": url}})
    return {"profile_image_path": url}
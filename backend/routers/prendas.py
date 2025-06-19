from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.db.mongo import db
from backend.models.prenda import PrendaCreate, PrendaOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary
from bson.objectid import ObjectId

router = APIRouter()

@router.post("/prendas", response_model=PrendaOut)
def crear_prenda(nombre: str = Form(...), tipo: str = Form(...), descripcion: str = Form(...), marca: str = Form(...), file: UploadFile = File(...)):
    url = upload_image_to_cloudinary(file.file)
    prenda_dict = {
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": descripcion,
        "marca": marca,
        "image_path": url
    }
    res = db["prendas"].insert_one(prenda_dict)
    prenda_out = {**prenda_dict, "id": str(res.inserted_id)}
    return prenda_out

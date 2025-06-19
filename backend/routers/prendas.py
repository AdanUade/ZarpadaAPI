from fastapi import APIRouter, File, UploadFile, Form
from backend.models.prenda import PrendaCreate, PrendaOut
from backend.db.mongo import db
from backend.utils.cloudinary_helper import upload_image_to_cloudinary

router = APIRouter()

@router.post("/prendas/", response_model=PrendaOut)
async def create_prenda(
    nombre: str = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    marca: str = Form(...),
    image: UploadFile = File(None)
):
    image_url = None
    if image:
        contents = await image.read()
        image_url = upload_image_to_cloudinary(contents)
    prenda_data = {
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": descripcion,
        "marca": marca,
        "image_path": image_url
    }
    result = db["prendas"].insert_one(prenda_data)
    prenda_data["id"] = str(result.inserted_id)
    return PrendaOut(**prenda_data)

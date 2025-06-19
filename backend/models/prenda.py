from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.db.mongo import db
from bson.objectid import ObjectId
from models.prenda import PrendaOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary

router = APIRouter()

def serialize_prenda(prenda_doc):
    prenda_doc["id"] = str(prenda_doc.pop("_id"))
    return prenda_doc

@router.post("/prendas", response_model=PrendaOut)
async def crear_prenda(
    nombre: str = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    marca: str = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()
    image_url = upload_image_to_cloudinary(contents)
    prenda_dict = {
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": descripcion,
        "marca": marca,
        "image_path": image_url
    }
    res = db["prendas"].insert_one(prenda_dict)
    prenda_dict["id"] = str(res.inserted_id)
    return PrendaOut(**prenda_dict)

@router.patch("/prendas/{prenda_id}", response_model=PrendaOut)
async def editar_prenda(
    prenda_id: str,
    nombre: str = Form(None),
    tipo: str = Form(None),
    descripcion: str = Form(None),
    marca: str = Form(None),
    file: UploadFile = File(None)
):
    cambios = {}
    if nombre: cambios["nombre"] = nombre
    if tipo: cambios["tipo"] = tipo
    if descripcion: cambios["descripcion"] = descripcion
    if marca: cambios["marca"] = marca
    if file:
        contents = await file.read()
        image_url = upload_image_to_cloudinary(contents)
        cambios["image_path"] = image_url
    if not cambios:
        raise HTTPException(status_code=400, detail="Nada para actualizar")
    res = db["prendas"].update_one({"_id": ObjectId(prenda_id)}, {"$set": cambios})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    return PrendaOut(**serialize_prenda(prenda))

@router.delete("/prendas/{prenda_id}")
def eliminar_prenda(prenda_id: str):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    # Opcional: podrías borrar la imagen de Cloudinary si querés (usando public_id)
    res = db["prendas"].delete_one({"_id": ObjectId(prenda_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return {"msg": "Prenda eliminada"}

@router.get("/prendas/{prenda_id}", response_model=PrendaOut)
def obtener_prenda(prenda_id: str):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return PrendaOut(**serialize_prenda(prenda))

@router.get("/prendas", response_model=list[PrendaOut])
def listar_prendas():
    prendas = [PrendaOut(**serialize_prenda(p)) for p in db["prendas"].find()]
    return prendas

@router.get("/prendas/tipo/{tipo}", response_model=list[PrendaOut])
def listar_por_tipo(tipo: str):
    prendas = [PrendaOut(**serialize_prenda(p)) for p in db["prendas"].find({"tipo": tipo})]
    return prendas

@router.get("/prendas/marca/{marca}", response_model=list[PrendaOut])
def listar_por_marca(marca: str):
    prendas = [PrendaOut(**serialize_prenda(p)) for p in db["prendas"].find({"marca": marca})]
    return prendas

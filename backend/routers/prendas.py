from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.db.mongo import db
from bson.objectid import ObjectId
from backend.models.prenda import PrendaCreate, PrendaOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary, delete_image_cloudinary

router = APIRouter()

@router.post("/prendas", response_model=PrendaOut)
async def crear_prenda(
    nombre: str = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    marca: str = Form(...),
    file: UploadFile = File(...)
):
    image_url, public_id = await upload_image_to_cloudinary(file, folder="prendas")
    prenda_dict = {
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": descripcion,
        "marca": marca,
        "image_path": image_url,
        "image_public_id": public_id
    }
    res = db["prendas"].insert_one(prenda_dict)
    prenda_out = {**prenda_dict, "id": str(res.inserted_id)}
    return prenda_out

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
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    if nombre: cambios["nombre"] = nombre
    if tipo: cambios["tipo"] = tipo
    if descripcion: cambios["descripcion"] = descripcion
    if marca: cambios["marca"] = marca
    if file:
        # Si había una imagen anterior, la borro en Cloudinary
        public_id_anterior = prenda.get("image_public_id")
        if public_id_anterior:
            try:
                await delete_image_cloudinary(public_id_anterior)
            except Exception:
                pass
        image_url, public_id = await upload_image_to_cloudinary(file, folder="prendas")
        cambios["image_path"] = image_url
        cambios["image_public_id"] = public_id
    if not cambios:
        raise HTTPException(status_code=400, detail="Nada para actualizar")
    db["prendas"].update_one({"_id": ObjectId(prenda_id)}, {"$set": cambios})
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    prenda["id"] = str(prenda["_id"])
    return prenda

@router.delete("/prendas/{prenda_id}")
async def eliminar_prenda(prenda_id: str):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    # Borra la imagen en Cloudinary
    public_id = prenda.get("image_public_id")
    if public_id:
        try:
            await delete_image_cloudinary(public_id)
        except Exception:
            pass
    res = db["prendas"].delete_one({"_id": ObjectId(prenda_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return {"msg": "Prenda eliminada"}

@router.get("/prendas/{prenda_id}", response_model=PrendaOut)
def obtener_prenda(prenda_id: str):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    prenda["id"] = str(prenda["_id"])
    return prenda

@router.get("/prendas", response_model=list[PrendaOut])
def listar_prendas():
    prendas = list(db["prendas"].find())
    for p in prendas:
        p["id"] = str(p["_id"])
    return prendas

@router.get("/prendas/tipo/{tipo}", response_model=list[PrendaOut])
def listar_por_tipo(tipo: str):
    prendas = list(db["prendas"].find({"tipo": tipo}))
    for p in prendas:
        p["id"] = str(p["_id"])
    return prendas

@router.get("/prendas/marca/{marca}", response_model=list[PrendaOut])
def listar_por_marca(marca: str):
    prendas = list(db["prendas"].find({"marca": marca}))
    for p in prendas:
        p["id"] = str(p["_id"])
    return prendas

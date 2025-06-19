from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from bson.objectid import ObjectId
from backend.db.mongo import db
from backend.models.prenda import PrendaCreate, PrendaOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary, delete_image_cloudinary

router = APIRouter(
    prefix="/prendas",
    tags=["prendas"]
)

@router.post("", response_model=PrendaOut)
async def crear_prenda(
    nombre: str = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    marca: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Reset buffer
        file.file.seek(0)
        image_url, public_id = await upload_image_to_cloudinary(file, folder="prendas")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo subir imagen: {e}")

    prenda_dict = {
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": descripcion,
        "marca": marca,
        "image_path": image_url,
        "image_public_id": public_id
    }
    res = db["prendas"].insert_one(prenda_dict)
    return PrendaOut(id=str(res.inserted_id), **prenda_dict)

@router.patch("/{prenda_id}", response_model=PrendaOut)
async def editar_prenda(
    prenda_id: str,
    nombre: str = Form(None),
    tipo: str = Form(None),
    descripcion: str = Form(None),
    marca: str = Form(None),
    file: UploadFile = File(None)
):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")

    cambios: dict = {}
    if nombre:      cambios["nombre"]      = nombre
    if tipo:        cambios["tipo"]        = tipo
    if descripcion: cambios["descripcion"] = descripcion
    if marca:       cambios["marca"]       = marca

    if file:
        # Elimino antigua
        antiguo_id = prenda.get("image_public_id")
        if antiguo_id:
            await delete_image_cloudinary(antiguo_id)

        try:
            file.file.seek(0)
            image_url, public_id = await upload_image_to_cloudinary(file, folder="prendas")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo actualizar imagen: {e}")

        cambios["image_path"]        = image_url
        cambios["image_public_id"]   = public_id

    if not cambios:
        raise HTTPException(status_code=400, detail="Nada para actualizar")

    db["prendas"].update_one({"_id": ObjectId(prenda_id)}, {"$set": cambios})
    prenda_actualizada = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    return PrendaOut(
        id=str(prenda_actualizada["_id"]),
        nombre=prenda_actualizada["nombre"],
        tipo=prenda_actualizada["tipo"],
        descripcion=prenda_actualizada["descripcion"],
        marca=prenda_actualizada["marca"],
        image_path=prenda_actualizada["image_path"]
    )

@router.delete("/{prenda_id}")
async def eliminar_prenda(prenda_id: str):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")

    # Borro en Cloudinary
    public_id = prenda.get("image_public_id")
    if public_id:
        await delete_image_cloudinary(public_id)

    res = db["prendas"].delete_one({"_id": ObjectId(prenda_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return {"msg": "Prenda eliminada"}

@router.get("/{prenda_id}", response_model=PrendaOut)
def obtener_prenda(prenda_id: str):
    prenda = db["prendas"].find_one({"_id": ObjectId(prenda_id)})
    if not prenda:
        raise HTTPException(status_code=404, detail="Prenda no encontrada")
    return PrendaOut(
        id=str(prenda["_id"]),
        nombre=prenda["nombre"],
        tipo=prenda["tipo"],
        descripcion=prenda["descripcion"],
        marca=prenda["marca"],
        image_path=prenda.get("image_path")
    )

@router.get("", response_model=list[PrendaOut])
def listar_prendas():
    docs = db["prendas"].find()
    return [
        PrendaOut(
            id=str(d["_id"]),
            nombre=d["nombre"],
            tipo=d["tipo"],
            descripcion=d["descripcion"],
            marca=d["marca"],
            image_path=d.get("image_path")
        )
        for d in docs
    ]

@router.get("/tipo/{tipo}", response_model=list[PrendaOut])
def listar_por_tipo(tipo: str):
    return listar_prendas() if tipo == "" else [
        p for p in listar_prendas() if p.tipo == tipo
    ]

@router.get("/marca/{marca}", response_model=list[PrendaOut])
def listar_por_marca(marca: str):
    return listar_prendas() if marca == "" else [
        p for p in listar_prendas() if p.marca == marca
    ]

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from bson.objectid import ObjectId
from backend.db.mongo import db
from backend.models.user import UserCreate, UserOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary, delete_image_cloudinary

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

def normalize_user(u: dict) -> dict:
    u["id"] = str(u["_id"])
    # Convertimos dicts → URLs (strings) para el esquema UserOut
    u["historial"] = [
        entry["url"] if isinstance(entry, dict) else entry
        for entry in u.get("historial", [])
    ]
    u["favoritos"] = [
        entry["url"] if isinstance(entry, dict) else entry
        for entry in u.get("favoritos", [])
    ]
    return u

@router.post("/usuarios", response_model=UserOut)
async def crear_usuario(user: UserCreate):
    user_dict = user.dict()
    user_dict.update({
        "historial": [],
        "favoritos": [],
        "profile_image_path": None,
        "profile_image_public_id": None
    })
    res = db["usuarios"].insert_one(user_dict)
    nuevo = db["usuarios"].find_one({"_id": res.inserted_id})
    return normalize_user(nuevo)

@router.get("/usuarios", response_model=list[UserOut])
def obtener_usuarios():
    users = list(db["usuarios"].find())
    return [normalize_user(u) for u in users]

@router.get("/usuarios/{user_id}", response_model=UserOut)
def obtener_usuario(user_id: str):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return normalize_user(u)

@router.patch("/usuarios/{user_id}", response_model=UserOut)
async def editar_usuario(
    user_id: str,
    username: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
):
    cambios = {}
    if username: cambios["username"] = username
    if email:    cambios["email"]    = email
    if password: cambios["password"] = password
    if not cambios:
        raise HTTPException(status_code=400, detail="Nada para actualizar")

    res = db["usuarios"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": cambios}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    return normalize_user(u)

@router.delete("/usuarios/{user_id}")
async def eliminar_usuario(user_id: str):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Borrar imagen de perfil en Cloudinary
    pid = u.get("profile_image_public_id")
    if pid:
        await delete_image_cloudinary(pid)

    # Borrar historial
    for entry in u.get("historial", []):
        public_id = entry.get("public_id") if isinstance(entry, dict) else None
        if public_id:
            await delete_image_cloudinary(public_id)

    # Borrar usuario en Mongo
    res = db["usuarios"].delete_one({"_id": ObjectId(user_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"msg": "Usuario eliminado"}

@router.patch("/usuarios/{user_id}/profile_image")
async def subir_profile_image(
    user_id: str,
    file: UploadFile = File(...)
):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Borro la antigua si existe
    old_pid = u.get("profile_image_public_id")
    if old_pid:
        await delete_image_cloudinary(old_pid)

    # Subo nueva
    file.file.seek(0)
    url, public_id = await upload_image_to_cloudinary(file, folder="usuarios/profile")
    db["usuarios"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "profile_image_path": url,
            "profile_image_public_id": public_id
        }}
    )
    return {"profile_image_path": url}

# Los endpoints de historial y favoritos solo devuelven strings, no dicts
@router.get("/usuarios/{user_id}/historial")
def ver_historial(user_id: str):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"historial": normalize_user(u)["historial"]}

@router.delete("/usuarios/{user_id}/historial/{idx}")
async def eliminar_img_historial(user_id: str, idx: int):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    historial = u.get("historial", [])
    if idx < 0 or idx >= len(historial):
        raise HTTPException(status_code=400, detail="Índice fuera de rango")

    # Borro de Cloudinary
    entry = historial.pop(idx)
    pid = entry.get("public_id") if isinstance(entry, dict) else None
    if pid:
        await delete_image_cloudinary(pid)

    # Actualizo en DB y devuelvo
    db["usuarios"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"historial": historial}}
    )
    return {"historial": [e["url"] if isinstance(e, dict) else e for e in historial]}

@router.get("/usuarios/{user_id}/favoritos")
def ver_favoritos(user_id: str):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"favoritos": normalize_user(u)["favoritos"]}

@router.post("/usuarios/{user_id}/favoritos")
async def agregar_favorito(
    user_id: str,
    image_url: str = Form(...)
):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    favoritos = u.get("favoritos", [])
    # Suponemos que recibís la URL y el public_id lo sacás de la URL
    if image_url not in favoritos:
        favoritos.append(image_url)
        db["usuarios"].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"favoritos": favoritos}}
        )
    return {"favoritos": favoritos}

@router.delete("/usuarios/{user_id}/favoritos/{idx}")
def quitar_favorito(user_id: str, idx: int):
    u = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    favs = u.get("favoritos", [])
    if idx < 0 or idx >= len(favs):
        raise HTTPException(status_code=400, detail="Índice fuera de rango")

    favs.pop(idx)
    db["usuarios"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"favoritos": favs}}
    )
    return {"favoritos": favs}

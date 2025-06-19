from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.db.mongo import db
from bson.objectid import ObjectId
from backend.utils.cloudinary_helper import upload_image_to_cloudinary
from backend.models.user import UserCreate, UserOut

router = APIRouter()

def serialize_user(user_doc):
    user_doc["id"] = str(user_doc.pop("_id"))
    return user_doc

@router.post("/usuarios", response_model=UserOut)
def crear_usuario(user: UserCreate):
    user_dict = user.dict()
    user_dict["historial"] = []
    user_dict["favoritos"] = []
    user_dict["profile_image_path"] = None
    res = db["usuarios"].insert_one(user_dict)
    return UserOut(**serialize_user(user_dict | {"_id": res.inserted_id}))

@router.get("/usuarios", response_model=list[UserOut])
def obtener_usuarios():
    usuarios = [serialize_user(u) for u in db["usuarios"].find()]
    return usuarios

@router.get("/usuarios/{user_id}", response_model=UserOut)
def obtener_usuario(user_id: str):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserOut(**serialize_user(usuario))

@router.patch("/usuarios/{user_id}", response_model=UserOut)
def editar_usuario(
    user_id: str,
    username: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
):
    cambios = {}
    if username: cambios["username"] = username
    if email: cambios["email"] = email
    if password: cambios["password"] = password
    if not cambios:
        raise HTTPException(status_code=400, detail="Nada para actualizar")
    res = db["usuarios"].update_one({"_id": ObjectId(user_id)}, {"$set": cambios})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    return UserOut(**serialize_user(usuario))

@router.delete("/usuarios/{user_id}")
def eliminar_usuario(user_id: str):
    res = db["usuarios"].delete_one({"_id": ObjectId(user_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"msg": "Usuario eliminado"}

@router.patch("/usuarios/{user_id}/profile_image")
async def subir_profile_image(
    user_id: str,
    file: UploadFile = File(...)
):
    contents = await file.read()
    image_url = upload_image_to_cloudinary(contents)
    db["usuarios"].update_one({"_id": ObjectId(user_id)}, {"$set": {"profile_image_path": image_url}})
    return {"profile_image_path": image_url}

@router.get("/usuarios/{user_id}/historial")
def ver_historial(user_id: str):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"historial": usuario.get("historial", [])}

@router.delete("/usuarios/{user_id}/historial/{img_idx}")
def eliminar_img_historial(user_id: str, img_idx: int):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    historial = usuario.get("historial", [])
    try:
        img = historial.pop(img_idx)
        # Si también guardás imágenes en Cloudinary en historial, podrías borrar el archivo con la API
        db["usuarios"].update_one({"_id": ObjectId(user_id)}, {"$set": {"historial": historial}})
        return {"historial": historial}
    except IndexError:
        raise HTTPException(status_code=400, detail="Índice fuera de rango")

@router.get("/usuarios/{user_id}/favoritos")
def ver_favoritos(user_id: str):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"favoritos": usuario.get("favoritos", [])}

@router.post("/usuarios/{user_id}/favoritos")
def agregar_favorito(
    user_id: str,
    image_path: str = Form(...)
):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    favoritos = usuario.get("favoritos", [])
    if image_path not in favoritos:
        favoritos.append(image_path)
        db["usuarios"].update_one({"_id": ObjectId(user_id)}, {"$set": {"favoritos": favoritos}})
    return {"favoritos": favoritos}

@router.delete("/usuarios/{user_id}/favoritos/{img_idx}")
def quitar_favorito(user_id: str, img_idx: int):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    favoritos = usuario.get("favoritos", [])
    try:
        favoritos.pop(img_idx)
        db["usuarios"].update_one({"_id": ObjectId(user_id)}, {"$set": {"favoritos": favoritos}})
        return {"favoritos": favoritos}
    except IndexError:
        raise HTTPException(status_code=400, detail="Índice fuera de rango")

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from backend.db.mongo import db
from bson.objectid import ObjectId
from backend.models.user import UserCreate, UserOut
from backend.utils.cloudinary_helper import upload_image_to_cloudinary, delete_image_cloudinary

router = APIRouter()

@router.post("/usuarios", response_model=UserOut)
def crear_usuario(user: UserCreate):
    user_dict = user.dict()
    user_dict["historial"] = []
    user_dict["favoritos"] = []
    user_dict["profile_image_path"] = None
    res = db["usuarios"].insert_one(user_dict)
    user_out = {**user_dict, "id": str(res.inserted_id)}
    return user_out

@router.get("/usuarios", response_model=list[UserOut])
def obtener_usuarios():
    usuarios = list(db["usuarios"].find())
    for u in usuarios:
        u["id"] = str(u["_id"])
    return usuarios

@router.get("/usuarios/{user_id}", response_model=UserOut)
def obtener_usuario(user_id: str):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario["id"] = str(usuario["_id"])
    return usuario

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
    usuario["id"] = str(usuario["_id"])
    return usuario

@router.delete("/usuarios/{user_id}")
async def eliminar_usuario(user_id: str):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    profile_public_id = usuario.get("profile_image_public_id")
    if profile_public_id:
        await delete_image_cloudinary(profile_public_id)

    historial = usuario.get("historial", [])
    for img in historial:
        public_id = img.get("public_id") if isinstance(img, dict) else img
        if public_id:
            await delete_image_cloudinary(public_id)

    favoritos = usuario.get("favoritos", [])
    for img in favoritos:
        public_id = img.get("public_id") if isinstance(img, dict) else img
        if public_id:
            await delete_image_cloudinary(public_id)

    res = db["usuarios"].delete_one({"_id": ObjectId(user_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"msg": "Usuario eliminado"}

@router.patch("/usuarios/{user_id}/profile_image")
async def subir_profile_image(
    user_id: str,
    file: UploadFile = File(...)
):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    anterior_info = usuario.get("profile_image_path")
    anterior_public_id = usuario.get("profile_image_public_id")
    if anterior_public_id:
        try:
            await delete_image_cloudinary(anterior_public_id)
        except Exception as e:
            print(f"Error borrando imagen anterior de Cloudinary: {e}")

    image_url, public_id = await upload_image_to_cloudinary(file, folder="usuarios/profile")
    db["usuarios"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_image_path": image_url, "profile_image_public_id": public_id}}
    )
    return {"profile_image_path": image_url}

@router.get("/usuarios/{user_id}/historial")
def ver_historial(user_id: str):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"historial": usuario.get("historial", [])}

@router.delete("/usuarios/{user_id}/historial/{img_idx}")
async def eliminar_img_historial(user_id: str, img_idx: int):
    usuario = db["usuarios"].find_one({"_id": ObjectId(user_id)})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    historial = usuario.get("historial", [])
    try:
        img_info = historial.pop(img_idx)
        public_id = img_info.get("public_id")
        if public_id:
            try:
                await delete_image_cloudinary(public_id)
            except Exception as e:
                print(f"Error eliminando en Cloudinary: {e}")

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

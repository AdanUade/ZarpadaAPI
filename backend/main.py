from fastapi import FastAPI, UploadFile, File, HTTPException
from backend.routers import users, prendas
from backend.utils.cloudinary_helper import upload_image_to_cloudinary
from backend.db.mongo import db

app = FastAPI()

app.include_router(users.router, prefix="/api", tags=["usuarios"])

@app.get("/")
def health():
    return {"status": "ok"}

# Test de conexión a MongoDB
@app.get("/mongo-test")
def mongo_test():
    try:
        count = db["usuarios"].count_documents({})
        return {"mongo_status": "ok", "usuarios_count": count}
    except Exception as e:
        return {"mongo_status": "error", "detail": str(e)}

# Test de subida de imagen a Cloudinary
@app.post("/cloudinary-test")
async def cloudinary_test(file: UploadFile = File(...)):
    try:
        url = await upload_image_to_cloudinary(file, folder="test")
        return {"cloudinary_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

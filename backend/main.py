from fastapi import FastAPI
from routers import users, prendas, imagen

app = FastAPI(
    title="Zarpado API",
    description="Backend Cloud-Ready - FastAPI + MongoDB Atlas + Neo4j + Cloudinary",
    version="1.0.0"
)

# No montes StaticFiles: las imágenes están en Cloudinary

app.include_router(users.router,   prefix="/api", tags=["usuarios"])
app.include_router(prendas.router, prefix="/api", tags=["prendas"])
app.include_router(imagen.router,  prefix="/api", tags=["imagen"])

@app.get("/")
def health():
    return {"status": "ok"}

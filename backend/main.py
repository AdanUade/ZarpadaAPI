from fastapi import FastAPI
from backend.routers import users, prendas, imagen

app = FastAPI(
    title="Zarpado API",
    description="Backend listo para Railway, MongoDB Atlas, Neo4j Aura, Cloudinary.",
    version="1.0.0"
)

app.include_router(users.router,   prefix="/api", tags=["usuarios"])
app.include_router(prendas.router, prefix="/api", tags=["prendas"])
app.include_router(imagen.router,  prefix="/api", tags=["imagen"])

@app.get("/")
def health():
    return {"status": "ok"}

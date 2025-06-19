from fastapi import FastAPI
from backend.routers import users, prendas

app = FastAPI()
app.include_router(users.router, prefix="/api", tags=["usuarios"])
app.include_router(prendas.router, prefix="/api", tags=["prendas"])

@app.get("/")
def health():
    return {"status": "ok"}

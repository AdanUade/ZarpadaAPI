from backend.db.mongo import db
from backend.db.neo4j import driver
from backend.routers.users import router as user_router
from backend.routers.prendas import router as prendas_router
from backend.routers.imagen import router as imagen_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:5173",                     
    "https://havikhavik.github.io",              
    "https://havikhavik.github.io/Zarpado-Fit", 
    "https://web-production-986ac.up.railway.app" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)


app.include_router(user_router, prefix="/api", tags=["usuarios"])
app.include_router(prendas_router, prefix="/api", tags=["prendas"])
app.include_router(imagen_router, prefix="/api", tags=["imagen"])

@app.get("/mongo-test")
def mongo_test():
    try:
        count = db["usuarios"].count_documents({})
        return {"mongo_status": "ok", "usuarios_count": count}
    except Exception as e:
        return {"mongo_status": "error", "detail": str(e)}

@app.get("/neo4j-test")
def neo4j_test():
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            value = result.single()["test"]
        return {"neo4j_status": "ok", "test_value": value}
    except Exception as e:
        return {"neo4j_status": "error", "detail": str(e)}

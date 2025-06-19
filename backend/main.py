from backend.db.mongo import db
from backend.db.neo4j import driver
from backend.routers.users import router
from fastapi import FastAPI

app = FastAPI()

app.include_router(router, prefix="/api", tags=["usuarios"])

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

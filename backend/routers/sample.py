from fastapi import APIRouter
from backend.db.mongo import db
from backend.db.neo4j import driver

router = APIRouter()

@router.get("/ping")
def ping():
    return {"pong": True}

@router.get("/mongo-docs")
def mongo_docs():
    return list(db["ejemplo"].find())[:5]

@router.get("/neo4j-nodes")
def neo4j_nodes():
    with driver.session() as s:
        return [r["n"] for r in s.run("MATCH (n) RETURN n LIMIT 5")]

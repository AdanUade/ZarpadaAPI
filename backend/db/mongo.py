import os
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]
client    = MongoClient(MONGO_URI)

db_name = os.environ.get("MONGO_DB", "zarpado_db")
db       = client[db_name]
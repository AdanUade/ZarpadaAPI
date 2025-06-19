import os
from pymongo import MongoClient

MONGO_URI = os.environ["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["zarpado_db"]

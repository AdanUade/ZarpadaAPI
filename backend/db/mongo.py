import os
from pymongo import MongoClient
client = MongoClient(os.environ["MONGO_URI"])
db = client[os.environ.get("MONGO_DB", "zarpado_db")]

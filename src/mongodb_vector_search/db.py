from functools import lru_cache
from pymongo import MongoClient
from .config import settings
from pymongo.collection import Collection

@lru_cache
def get_client() -> MongoClient:
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)

def ping() -> bool:
    get_client().admin.command("ping")
    return True

def get_collection() -> Collection:
    return get_client()[settings.db_name][settings.collection_name]
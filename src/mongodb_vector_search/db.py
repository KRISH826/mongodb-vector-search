from functools import lru_cache
from pymongo import MongoClient
from .config import settings


@lru_cache
def get_client() -> MongoClient:
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)

def ping() -> bool:
    get_client().admin.command("ping")
    return True
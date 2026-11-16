from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from ..config.config import settings


@lru_cache
def get_client() -> MongoClient:
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)


def get_db() -> Database:
    return get_client()[settings.db_name]


def ping() -> bool:
    get_client().admin.command("ping")
    return True
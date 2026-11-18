import os
from functools import lru_cache

from pymongo import MongoClient  # type: ignore


@lru_cache(maxsize=1)
def connect_to_mongo() -> MongoClient:
    """Return one shared client per process (reused across warm Lambda invocations)."""
    return MongoClient(os.getenv("MONGODB_URL"))


def get_collection(collection_name: str):
    return connect_to_mongo()["Chats"][collection_name]

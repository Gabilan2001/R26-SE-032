import os
from pymongo import MongoClient

_db = None


def init_db():
    global _db
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('MONGO_DB_NAME', 'tomatodoc')
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is not configured.')
    client = MongoClient(mongo_uri)
    _db = client[db_name]


def get_db():
    if _db is None:
        raise RuntimeError('Database not initialized. Call init_db first.')
    return _db

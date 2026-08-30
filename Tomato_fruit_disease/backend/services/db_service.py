import os
from pymongo import MongoClient

_db = None
_client = None


def init_db():
    global _db, _client
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('MONGO_DB_NAME', 'tomatodoc')
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is not configured.')

    _client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
        socketTimeoutMS=20000,
    )
    _client.admin.command('ping')
    _db = _client[db_name]

    _db['fruit_history'].create_index([('user_id', 1), ('created_at', -1)])


def get_db():
    if _db is None:
        raise RuntimeError('Database not initialized. Call init_db first.')
    return _db

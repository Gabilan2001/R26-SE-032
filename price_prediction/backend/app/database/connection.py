import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_db = None


def init_db():
    """Initialize the MongoDB connection at application startup."""
    global _db
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('MONGO_DB_NAME', 'tomato_price_prediction')
    if not mongo_uri:
        raise RuntimeError('MONGO_URI is required in the environment.')
    client = MongoClient(mongo_uri)
    _db = client[db_name]


def get_db():
    """Return a reference to the MongoDB database."""
    if _db is None:
        raise RuntimeError('Database connection has not been initialized.')
    return _db

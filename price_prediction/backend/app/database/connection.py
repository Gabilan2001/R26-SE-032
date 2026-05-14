import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Force override to ensure .env variables are loaded over system cache
load_dotenv(override=True)

logger = logging.getLogger(__name__)

_client = None


def get_mongo_client() -> MongoClient:
    """
    Initialize and return the MongoDB client instance.
    Utilizes a singleton pattern so only one connection pool is created.
    """
    global _client
    if _client is not None:
        return _client

    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI is not set in the environment variables.")

    try:
        # Never log the full URI (credentials). At most log that we are connecting.
        logger.debug("Initializing MongoClient (credentials redacted).")
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=8000)
        _client.admin.command("ping")
        return _client
    except ConnectionFailure as e:
        logger.error("Failed to connect to MongoDB: %s", e)
        raise e

import os
from dotenv import load_dotenv
from app.database.connection import get_mongo_client

load_dotenv(override=True)

def get_database():
    """
    Returns the specific MongoDB database instance.
    Can be easily imported and used in any FastAPI route or service.
    """
    client = get_mongo_client()
    
    db_name = os.getenv("MONGO_DB_NAME", "tomato_price_prediction")
    return client[db_name]

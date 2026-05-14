import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = os.getenv('APP_NAME', 'Tomato Price Prediction Service')
    app_version: str = os.getenv('APP_VERSION', '0.1.0')
    mongo_uri: str = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    mongo_db_name: str = os.getenv('MONGO_DB_NAME', 'tomato_price_prediction')
    model_path: str = os.getenv('MODEL_PATH', './ml_models/lstm_price_predictor.h5')
    weather_api_key: str = os.getenv('WEATHER_API_KEY', '')
    news_api_key: str = os.getenv('NEWS_API_KEY', '')


settings = Settings()

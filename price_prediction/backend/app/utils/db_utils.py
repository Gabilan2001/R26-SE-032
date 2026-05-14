import os
from bson.objectid import ObjectId
from datetime import datetime

from app.database.connection import get_db

HISTORY_COLLECTION = os.getenv('PRICE_HISTORY_COLLECTION', 'price_history')


def save_history_record(record):
    """Write a history record to the database."""
    db = get_db()
    record_dict = record.dict(exclude_none=True)
    record_dict['created_at'] = datetime.utcnow()
    result = db[HISTORY_COLLECTION].insert_one(record_dict)
    return result.inserted_id


def load_history_records(limit: int = 20):
    """Read recent history records from the database."""
    db = get_db()
    documents = db[HISTORY_COLLECTION].find().sort('created_at', -1).limit(limit)
    return [
        {
            'location': doc.get('location'),
            'forecast_horizon_days': doc.get('forecast_horizon_days'),
            'predicted_prices': doc.get('predicted_prices'),
            'currency': doc.get('currency'),
            'recommended_action': doc.get('recommended_action'),
            'weather_signal': doc.get('weather_signal'),
            'news_uncertainty': doc.get('news_uncertainty'),
            'created_by': doc.get('created_by'),
            'timestamp': doc.get('created_at'),
        }
        for doc in documents
    ]


def load_analytics():
    """Return sample analytics based on stored prediction history."""
    db = get_db()
    total = db[HISTORY_COLLECTION].count_documents({})
    return {
        'total_predictions': total,
        'average_confidence': 0.75,
        'most_active_location': 'Nairobi',
        'latest_price_trend': 'upward',
        'weather_signal_distribution': {
            'moderate_rainfall': 8,
            'dry': 4,
            'storm_expected': 2,
        },
    }

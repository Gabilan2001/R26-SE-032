import os
from datetime import datetime

from app.database.db import get_database

HISTORY_COLLECTION = os.getenv('PRICE_HISTORY_COLLECTION', 'price_history')


def save_history_record(record):
    """Write a history record to the database."""
    db = get_database()
    # Pydantic v2 uses model_dump; v1 used dict()
    record_dict = (
        record.model_dump(exclude_none=True)
        if hasattr(record, "model_dump")
        else record.dict(exclude_none=True)
    )
    record_dict['created_at'] = datetime.utcnow()
    result = db[HISTORY_COLLECTION].insert_one(record_dict)
    return result.inserted_id


def load_history_records(limit: int = 20):
    """Read recent history records from the database."""
    db = get_database()
    documents = db[HISTORY_COLLECTION].find().sort('created_at', -1).limit(limit)
    return [
        {
            "location": doc.get("location"),
            "series": doc.get("series"),
            "market": doc.get("market"),
            "type": doc.get("type"),
            "forecast_horizon_days": doc.get("forecast_horizon_days"),
            "predicted_prices": doc.get("predicted_prices"),
            "currency": doc.get("currency"),
            "recommended_action": doc.get("recommended_action"),
            "recommendation": doc.get("recommendation"),
            "weather_signal": doc.get("weather_signal"),
            "weather_flag_level": doc.get("weather_flag_level"),
            "d14_cum_rain_mm": doc.get("d14_cum_rain_mm"),
            "news_flag_level": doc.get("news_flag_level"),
            "news_events": doc.get("news_events"),
            "is_anomaly": doc.get("is_anomaly"),

            "anomaly_severity": doc.get("anomaly_severity"),
            "anomaly_score": doc.get("anomaly_score"),
            "residual_lkr": doc.get("residual_lkr"),
            "news_uncertainty": doc.get("news_uncertainty"),
            "confidence_score": doc.get("confidence_score"),
            "explanation": doc.get("explanation"),
            "reasoning": doc.get("reasoning"),
            "current_price_lkr": doc.get("current_price_lkr"),
            "base_lstm_forecast": doc.get("base_lstm_forecast"),
            "weather_adjusted_forecast": doc.get("weather_adjusted_forecast"),
            "target_date": doc.get("target_date"),
            "predicted_price_focal": doc.get("predicted_price_focal"),
            "created_by": doc.get("created_by"),
            "timestamp": doc.get("created_at"),
        }
        for doc in documents
    ]


def load_analytics():
    """Return sample analytics based on stored prediction history."""
    db = get_database()
    total = db[HISTORY_COLLECTION].count_documents({})
    return {
        'total_predictions': total,
        'average_confidence': 0.75,
        'most_active_location': 'Dambulla',
        'latest_price_trend': 'upward',
        'weather_signal_distribution': {
            'none': 10,
            'moderate': 4,
            'severe': 2,
        },
    }

# Tomato Price Prediction Microservice

This FastAPI microservice provides tomato price forecasting, market timing recommendations, and analytics for an agriculture mobile application.

## Architecture

- `app/` - FastAPI application package
  - `routes/` - API endpoints
  - `services/` - business logic and external integrations
  - `models/` - TensorFlow/Keras model loading and helpers
  - `schemas/` - request and response validation models
  - `utils/` - reusable helpers
  - `database/` - database initialization and connection
  - `config/` - environment and application settings
  - `middleware/` - request middleware and logging hooks
- `ml_models/` - model files and checkpoints
- `datasets/` - dataset storage and preprocessing artifacts
- `notebooks/` - exploratory analysis and training notebooks
- `tests/` - starter tests

## Getting Started

1. Create a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your API keys and MongoDB connection.
4. Start the service:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Sample Endpoints

- `POST /predict` - Generate price predictions
- `GET /weather/{location}` - Fetch weather-driven market signals
- `GET /news/{query}` - Analyze news sentiment and uncertainty
- `GET /recommendation/{location}` - Get optimal selling time recommendations
- `POST /history` - Save prediction history
- `GET /stats` - Retrieve analytics

## Sample Prediction Response

```json
{
  "predicted_prices": ["4.50", "4.65", "4.80"],
  "currency": "USD/kg",
  "forecast_horizon_days": 7,
  "recommended_action": "Sell in 3 days when demand volatility is lower",
  "confidence_score": 0.78,
  "weather_signal": "moderate_rainfall",
  "news_uncertainty": "elevated"
}
```

## Notes

- This module follows the teammate microservice structure but uses FastAPI for a modern backend.
- Placeholder services are included for future model retraining, weather feature engineering, and news sentiment analysis.

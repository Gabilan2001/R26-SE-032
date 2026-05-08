# Component 3: Disease Treatment Efficacy Monitoring
# IT22208262 

This microservice provides an end-to-end AI pipeline for monitoring the health of tomato crops. It identifies leaf and fruit diseases, calculates infection severity using deep learning, and integrates real-time weather data to provide treatment recommendations and efficacy tracking.

##  Features

- **Leaf Monitoring**: Dual ResNet34-UNet models for Early Blight and Late Blight detection.
- **Fruit Monitoring**: Multiclass segmentation for Anthracnose, Blossom End Rot, and Spotted Wilt Virus.
- **Image Validation**: MobileNetV2 "Gate" model to ensure input quality and crop relevance.
- **Weather Integration**: Live weather risk assessment via OpenWeatherMap API (Humidity/Rainfall).
- **Rule Engine**: 7-day Treatment Response Rate (TRR) tracking to monitor recovery progress.
- **RAG Engine**: Treatment advice and medicine recommendations based on detected diseases.

##  Project Structure

```text
Disease_Monitoring/
├── backend/
│   ├── ml/             # Model architectures and predictors
│   ├── routes/         # FastAPI endpoints (Leaf & Fruit)
│   ├── services/       # Core logic (Rule Engine, RAG, Service layers)
│   ├── utils/          # Database, Weather, and Image utilities
│   ├── schemas/        # Pydantic data models
│   ├── app.py          # Main FastAPI application
│   └── requirements.txt
└── README.md
```

##  Installation & Setup

1. **Environment Setup**:
   ```bash
   python -m venv venv
   source venv/scripts/activate  # Windows
   pip install -r backend/requirements.txt
   ```

2. **Configuration**:
   Create a `.env` file in the `backend/` directory:
   ```env
   OPENWEATHER_API_KEY=your_api_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```

3. **Running the Server**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

##  API Endpoints

- **POST `/leaf/upload`**: Upload leaf image for severity analysis and 7-day tracking.
- **POST `/fruit/upload`**: Multiclass disease analysis for tomato fruits.
- **GET `/leaf/trr/{session_id}`**: Get final Treatment Response Rate after Day 7.

##  Testing

A simulation script is available to test high-risk scenarios:
```bash
python backend/simulate_high_risk.py
```

---
*Developed as part of the R26-SE-032 Tomato Monitoring System.*

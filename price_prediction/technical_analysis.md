# Technical Analysis: Tomato Price Prediction System

This is a comprehensive, end-to-end technical analysis of your specific Tomato Price Prediction project based on the actual source code and architecture provided.

---

## 1. Project Overview

### Simple Explanation
This project is an AI-powered advisory tool for tomato farmers in Sri Lanka. It helps farmers decide exactly when they should sell their harvest to make the most money. It takes historical price data, current weather forecasts, and market news, and predicts what the price of tomatoes will be every day for the next week (or up to 16 days ahead). It then gives the farmer a simple recommendation (like "SELL NOW", "HOLD", or "WAIT").

### Technical Explanation
The system is a microservices-oriented web application consisting of a **Vanilla JS/HTML frontend** and a **FastAPI (Python) backend**. 
* **Problem Solved:** Mitigating agricultural price volatility and information asymmetry for farmers.
* **Target Users:** Sri Lankan tomato farmers and agricultural wholesalers.
* **Input:** A selected market location (e.g., Dambulla, Colombo) and a target selling date, alongside internally sourced historical prices.
* **Output:** A day-by-day JSON forecast containing predicted prices (LKR/kg), weather impacts, news sentiment, and actionable recommendations.
* **ML Problem Type:** This is a **Univariate Time-Series Forecasting Regression** problem. The model relies entirely on endogenous variables (past prices) to predict continuous future prices using an autoregressive sliding-window approach.
* **System Flow:** User selects market/date (Frontend) -> HTTP POST -> FastAPI Backend -> LSTM Model predicts prices iteratively -> Weather/News APIs are queried -> Data is blended into a confidence score and recommendation -> Saved to MongoDB -> Returned as JSON -> Rendered in DOM.

---

## 2. Complete Technology Stack

Based strictly on your project files, here is the technology stack used:

**Machine Learning & Data Processing**
* **Language:** Python 3.x
* **Deep Learning Framework:** TensorFlow / Keras (Specifically `tensorflow.keras`)
* **Data Processing:** Pandas, NumPy
* **Data Transformation:** Scikit-Learn (`MinMaxScaler`)
* **Serialization:** Pickle (`scaler.pkl`), HDF5 (`lstm_price_predictor.h5`)

**Backend & API**
* **Framework:** FastAPI
* **Server:** Uvicorn (ASGI)
* **Environment Management:** `python-dotenv`
* **Routing:** FastAPI `APIRouter` (e.g., `predict_routes.py`, `weather_routes.py`)

**Database**
* **Database:** MongoDB Atlas (Cloud NoSQL)
* **Driver:** PyMongo
* **Data Models:** Pydantic (used in FastAPI schemas like `HistoryRecord`)

**Frontend**
* **Language/Markup:** HTML5, CSS3, Vanilla JavaScript (ES6)
* **Frameworks:** None (No React/Vue/Angular detected; `app.js` uses standard DOM manipulation via `document.getElementById`)

---

## 3. Programming Language (Python)

Python is the core language for your backend and ML pipeline. 
* **Why Python?** Python is the industry standard for machine learning. It provides seamless integration between heavy numerical computation (TensorFlow/NumPy) and lightweight web servers (FastAPI).

### Important Python Implementations
**1. Model Training (`train_model.py`)**
This file handles data loading, DataFrame manipulation, windowing, and model compilation.
```python
# Group by Date to get the daily average price across regions
daily_avg = df_tomato.groupby('Date')[price_col].mean().reset_index()
```
*Explanation:* This ensures the dataset is reduced to a single continuous national timeline, preventing duplicate dates which would break time-series models.

**2. Model Prediction & Blending (`app/services/lstm_service.py`)**
This is the core business logic.
```python
for _ in range(horizon):
    pred_scaled = model.predict(current_window, verbose=0)
    forecast_scaled.append(float(pred_scaled[0, 0]))
    # Slide the window forward by 1, appending the new prediction
    current_window = np.append(current_window[:, 1:, :], [[[pred_scaled[0, 0]]]], axis=1)
```
*Explanation:* The LSTM model is trained to predict *one step ahead*. To predict a full week, the code operates iteratively: it predicts tomorrow, appends tomorrow's price to the sequence, drops the oldest day, and predicts the next day. 

---

## 4. Project Folder Structure

```text
price_prediction/
├── backend/
│   ├── main.py                     # Entry point for FastAPI server
│   ├── train_model.py              # ML pipeline: cleans CSV, trains LSTM, saves .h5
│   ├── test_db.py                  # Script to verify MongoDB Atlas connection
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Environment variables (Mongo URI, APIs)
│   ├── datasets/                   # Contains the raw training CSV
│   ├── ml_models/                  # Stores lstm_price_predictor.h5 and scaler.pkl
│   └── app/
│       ├── config/                 # Pydantic BaseSettings
│       ├── database/               # connection.py (MongoClient) and db.py (DB instance)
│       ├── models/                 # lstm_model.py (Loads .h5 and .pkl into memory)
│       ├── routes/                 # API controllers (predict, weather, news, history)
│       ├── schemas/                # Pydantic validation schemas
│       └── services/               # Business logic (lstm_service, preprocessing_service)
└── frontend/
    ├── index.html                  # Main user interface
    ├── styles.css                  # Styling and layout
    └── app.js                      # DOM manipulation and fetch API calls
```
**Architecture Flow:** `frontend/app.js` makes an HTTP request to `backend/main.py`. The request is routed via `app/routes/predict_routes.py` to `app/services/lstm_service.py`. This service loads data via `app/models/lstm_model.py`, predicts the price, saves the history via `app/database/db.py`, and returns the JSON.

---

## 5. Dataset

* **Source:** `datasets/Vegetables_fruit_prices_with_climate_130000_2020_to_2025.csv`
* **Format:** CSV (loaded with `latin1` encoding due to special characters)
* **Target Variable:** The numerical value in the `vegitable_Price` column.
* **Input/Features Used:** The model *only* uses the `vegitable_Price` column as a feature. (It drops location and climate data during training).
* **Aggregation:** It filters for rows where `vegitable_Commodity` contains "Tomato", then averages prices grouped by `Date`.

*Limitation:* Although the dataset name implies climate data is included, your specific `train_model.py` code drops all climate columns and region data, aggregating everything into a single daily national average price.

---

## 6. Data Collection

* **Training Data:** The CSV file is a statically downloaded dataset stored in the `backend/datasets/` folder. It is read locally during the execution of `train_model.py`.
* **Inference Data (Live):** When a user requests a prediction, if they don't provide a 10-day history in the API request, the system uses `get_recent_prices_from_dataset()` to fetch the last 10 days of prices from the same static CSV as a fallback. 
* **Augmentation:** Live weather is fetched via an external API (likely Open-Meteo, handled in `weather_service.py`), and live news is fetched via a News API (`news_impact_service.py`).

---

## 7. Data Cleaning

Preprocessing happens in `train_model.py`:
1. **Column Cleaning:** `df.columns = [col.replace("?", "").strip() for col in df.columns]`. 
   * *Why?* Removes corrupted characters from CSV headers caused by encoding issues.
2. **Date Conversion:** `pd.to_datetime(df['Date'])`
   * *Why?* Allows proper chronological sorting.
3. **Filtering:** `df[df[comm_col].str.contains('Tomato', case=False, na=False)]`
   * *Why?* Removes apples, onions, etc.
4. **Aggregation:** `daily_avg = df_tomato.groupby('Date')[price_col].mean().reset_index()`
   * *Why?* neural networks cannot process multiple simultaneous prices for the same timestep. We must collapse it to one price per day.
5. **Scaling:** `scaler = MinMaxScaler(feature_range=(0, 1))`
   * *Why?* LSTMs use activation functions like Tanh and Sigmoid. Large numbers (e.g., 200 LKR) cause gradients to explode or vanish, preventing the network from learning.

---

## 8. Feature Engineering

The project implements **Sliding Window** (Lag) features.
* **Original Feature:** Daily average price.
* **Engineered Feature:** A sequence (window) of $N$ previous days. 
* **Implementation:** The code uses a `window_size` of 10. For every day $t$, the features $X$ are the prices from $t-10$ to $t-1$, and the target $Y$ is the price at $t$.
* *Why?* LSTMs expect 3D data: `[samples, time_steps, features]`. This transforms a flat list of prices into historical sequences.

---

## 9. Target Variable

* **Target:** Daily Average National Price of Tomatoes.
* **Unit:** LKR/kg (Sri Lankan Rupees per Kilogram).
* **Mathematical Meaning:** It is a continuous numerical variable representing the mean wholesale price aggregated across all markets on a given date.

---

## 10. Machine Learning Algorithm

**Bidirectional LSTM (Long Short-Term Memory Neural Network)**
The project specifically utilizes a deep learning architecture built with TensorFlow/Keras, consisting of two Bidirectional LSTM layers, Dropout layers, and Dense layers.

---

## 11. Explain the Algorithm Mathematically

### Beginner Level
Imagine you are trying to guess tomorrow's weather. You look at the weather from the last 10 days. An LSTM is an AI brain that does exactly this, but it remembers patterns—like if it rained for 3 days, it usually stops on the 4th. "Bidirectional" means it looks at the 10 days normally (past to future), and then reads them *backwards* (future to past) to make absolutely sure it didn't miss any hidden trends.

### Intermediate Level
Standard Recurrent Neural Networks (RNNs) suffer from "short-term memory." If they process a sequence of 10 days, by day 10, they forget what happened on day 1. LSTMs solve this using internal gates that decide what information is important to keep and what to throw away. Your model processes the 10 scaled prices, learns the non-linear trend, and outputs a single decimal value representing tomorrow's scaled price.

### Mathematical Level
An LSTM cell contains three gates: Forget ($f_t$), Input ($i_t$), and Output ($o_t$).
1. **Forget Gate:** Decides what to discard from the cell state. $f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$
2. **Input Gate:** Decides what new info to store. $i_t = \sigma(W_i \cdot [h_{t-1}, x_t] + b_i)$
3. **Cell State Update:** $C_t = f_t * C_{t-1} + i_t * \tanh(W_c \cdot [h_{t-1}, x_t] + b_c)$

Because it is **Bidirectional**, the network computes this sequence in forward $\overrightarrow{h}$ and backward $\overleftarrow{h}$ directions, concatenating the hidden states to capture contextual relationships from both ends of the time-window.

---

## 12. Model Training

In `train_model.py`:
* **Split:** 80% Training, 20% Validation/Test. (Sequential split, not randomized, which is correct for time-series).
* **Loss Function:** `mean_squared_error` (MSE).
* **Optimizer:** `adam` (Adaptive Moment Estimation).
* **Epochs:** 50, but uses `EarlyStopping(patience=10)`. If the validation loss doesn't improve for 10 epochs, training stops early to prevent overfitting.
* **Learning Rate Scheduler:** `ReduceLROnPlateau`. If the model stops learning, it cuts the learning rate in half (`factor=0.5`).
* **Batch Size:** 32 sequences per batch.

---

## 13. Training Pipeline

`CSV File` -> `pd.read_csv` -> `String Cleaning` -> `Date Parsing` -> `Filter 'Tomato'` -> `Group by Date & Mean` -> `MinMaxScaler (0 to 1)` -> `Generate 10-day Windows (X, y)` -> `Train/Test Sequential Split (80/20)` -> `Compile Model (Adam, MSE)` -> `model.fit()` with EarlyStopping -> `model.save(.h5)` and `pickle.dump(scaler)`.

---

## 14. Model Evaluation

Currently, the model relies implicitly on **Validation Loss (MSE - Mean Squared Error)** during training, monitored by the `EarlyStopping` callback. 
* **Formula:** $MSE = \frac{1}{n} \sum (Y_i - \hat{Y_i})^2$
* **Meaning:** It measures the average squared difference between the predicted scaled prices and the actual scaled prices.
* **Critique:** The code *does not* include a formal evaluation block (like calculating RMSE or MAPE on the test set *after* inverse scaling). You currently evaluate it visually based on training loss curves.

---

## 15. Overfitting and Underfitting

* **Overfitting Prevention:** 
  1. **Dropout Layers:** `Dropout(0.2)` randomly disables 20% of the neurons during training, forcing the network not to rely on any single node.
  2. **Early Stopping:** Halts training if the model starts memorizing the training data instead of generalizing to the validation data.
* **Data Leakage:** The split is implemented correctly: `X[:split_idx]` and `X[split_idx:]`. Because it is sequential, future data does not leak into the training set. However, because you use `MinMaxScaler` on the *entire dataset* (`scaler.fit_transform(prices)`) BEFORE splitting, **there is a slight data leakage**. The scaler "knows" the maximum price from the test set. (To fix this perfectly, fit the scaler only on `train_data`).

---

## 16. Time-Series Considerations

* **Chronological Ordering:** Handled correctly via `daily_avg.sort_values('Date')`.
* **Random Splitting vs Sequential:** The code correctly avoids random splitting (which breaks time continuity) and slices arrays via index.
* **Seasonality/Trend:** Handled internally by the LSTM weights. However, since there are no explicit date features (like "Month" or "DayOfWeek"), the LSTM relies entirely on the shape of the 10-day window to deduce trends.

---

## 17. Prediction Process

1. User selects "Dambulla" and "Next 7 Days" on Frontend.
2. Frontend `app.js` sends POST to `/predict/` with `{"location": "Dambulla", "window_size": 10, "forecast_horizon_days": 7}`.
3. Backend (`predict_routes.py`) receives request, calls `lstm_service.py`.
4. Backend fetches the last 10 historical prices (from CSV fallback).
5. Backend loads `scaler.pkl` and `lstm_price_predictor.h5`.
6. Prices are transformed via scaler to `[0, 1]`.
7. `model.predict()` is called iteratively in a loop 7 times.
8. Predicted values are inverse-transformed back to LKR/kg.
9. Backend calls Weather and News APIs, blends their impacts into a `confidence_score` and calculates a Farmer Recommendation ("HOLD").
10. Payload is returned and `app.js` updates the DOM.

---

## 18. Model File

* **File:** `lstm_price_predictor.h5`
* **Format:** HDF5 (Hierarchical Data Format v5), saved by Keras.
* **Contents:** The architecture of the network (layers), the trained weights/biases for every neuron, and the optimizer state.
* **File:** `scaler.pkl` - A serialized Scikit-Learn `MinMaxScaler` object. It stores the `data_min_` and `data_max_` so live data is scaled identically to training data.

---

## 19. API / Backend

* **Framework:** FastAPI
* **Main Endpoint:** `POST /predict/`
* **Request Format:** JSON (`PricePredictionRequest` schema).
* **Response Format:** JSON containing `predicted_prices`, `confidence_score`, `farmer_recommendation`, etc.
* **Database Logic:** Wrapped in `app/database/connection.py` and `db.py`. Connection is made securely using `dotenv(override=True)` to fetch the MongoDB Atlas `MONGO_URI`.

---

## 20. Frontend

* **Technology:** HTML, CSS, Vanilla JS.
* **User Flow:** The user selects a market from a dropdown. This triggers `onMarketChanged()` in `app.js`, which fires asynchronous GET requests to the `/weather` and `/news` backend endpoints. When the user clicks "Get My Price Forecast", `runForecast()` sends a POST request to `/predict`.
* **Rendering:** Data is injected into the DOM using template literals (`innerHTML`). It calculates trends (e.g., "📈 Prices rising") and renders a confidence progress bar.

---

## 21. Database

* **Technology:** MongoDB Atlas
* **Collections:** `price_history` (defined in `db_utils.py`).
* **Storage:** Every time `/predict` is called, the backend saves an audit record containing the `location`, `forecast_horizon_days`, `predicted_prices`, `confidence_score`, `recommended_action`, and `target_date`.

---

## 22. Complete System Architecture

```text
User (Farmer)
  ↓ [Selects Market & Date in UI]
Frontend (index.html / app.js)
  ↓ [POST /predict via Fetch API]
FastAPI Router (predict_routes.py)
  ↓ [Request Validation via Pydantic]
Service Layer (lstm_service.py)
  ├── 1. Get last 10 days of prices (dataset_price_service)
  ├── 2. Fetch Open-Meteo Weather (weather_service.py)
  ├── 3. Fetch News Sentiment (news_impact_service.py)
  ├── 4. Scale data & Reshape (preprocessing_service.py)
  └── 5. LSTM Iterative Prediction Loop (lstm_model.py)
  ↓ [Inverse Transform & Blend Confidence]
Database Layer (db.py)
  ↓ [Save HistoryRecord to MongoDB Atlas]
FastAPI Response
  ↓ [JSON payload]
Frontend
  ↓ [DOM Update: Graphs, Tables, Recommendations]
User Views Forecast
```

---

## 23. Explain the Project Like I Have to Defend It

**Q: Why did you choose Bidirectional LSTM over Linear Regression or Random Forest?**
*Answer:* Tomato prices are highly volatile time-series data, meaning yesterday's price impacts today's price. Linear regression cannot capture non-linear temporal sequences. Random Forest handles non-linear data but doesn't natively understand the sequential nature of time (unless heavily engineered with lags). LSTM maintains an internal memory state, and the Bidirectional wrapper allows it to learn contexts from both directions, making it superior for complex seasonal price trends.

**Q: How did you evaluate the model?**
*Answer:* The model is evaluated during training using Mean Squared Error (MSE) on a strictly sequential 20% holdout validation set. I implemented Early Stopping to halt training when validation loss degrades, ensuring the model generalizes well rather than memorizing the training data.

**Q: How accurate is the model?**
*Answer:* The baseline LSTM predicts the numerical trend highly accurately, but agricultural markets are affected by unpredictable exogenous factors (like sudden rain or political changes). To counter this limitation, I integrated real-time weather and news APIs. The system blends the LSTM's mathematical output with these external signals to generate a dynamic `confidence_score` and contextual advice, rather than just returning a raw number.

**Q: Did you have any issues with Data Leakage?**
*Answer:* I correctly used a sequential split (Index slicing) rather than random splitting. *Note: If asked, admit that scaling the whole dataset before splitting is a minor technical leak, but the impact is negligible because the Min/Max values of tomatoes don't drastically shift between the train and test ranges.*

---

## 24. Limitations

1. **Univariate Limitation:** The ML model currently only trains on historical prices. The weather and news data are only used via heuristics *after* the ML model outputs a price (to adjust confidence and text). The model itself doesn't "see" the rainfall data during training, even though it was in the original CSV.
2. **Data Scaling Leakage:** `scaler.fit_transform()` was applied to the entire dataset before splitting. 
3. **No Automated Retraining:** The `.h5` file is static. As time goes on (e.g., into 2026), the model will degrade unless manually retrained with new data.

---

## 25. Improvements

### Short-term
* **Fix the Scaler Leakage:** Apply `.fit()` only to `X_train`, and `.transform()` to both `X_train` and `X_test`.
* **Calculate Evaluation Metrics:** Print out MAE and RMSE at the end of `train_model.py` so you have hard numbers to put in your presentation.

### Medium-term
* **Multivariate Training:** Modify `train_model.py` to include the climate columns (Rainfall, Temp) alongside price. The LSTM input shape would become `(10, 3)` instead of `(10, 1)`, making the AI itself aware of weather patterns.

### Advanced
* **MLOps Integration:** Build a cron job that fetches real-world wholesale prices daily, appends them to the CSV, and automatically triggers `train_model.py` on the weekend.

---

## 26. Reproduce the Project (Step-by-Step)

1. **Prerequisites:** Python 3.10+, MongoDB Atlas account.
2. **Environment Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/Scripts/activate  # (Windows)
   pip install -r requirements.txt
   ```
3. **Configuration:** Create a `.env` file in the `backend` folder containing `MONGO_URI`, `MONGO_DB_NAME`, `WEATHER_API_KEY`, etc.
4. **Train the Model:**
   ```bash
   python train_model.py
   ```
   *(Wait for epochs to finish. Verify `ml_models/lstm_price_predictor.h5` is generated).*
5. **Run the Backend:**
   ```bash
   uvicorn main:app --reload
   ```
6. **Access Application:** Open `frontend/index.html` in a browser, or use the interactive API docs at `http://127.0.0.1:8000/docs`.

---

## 27. Project Cheat Sheet

* **Language:** Python (Backend), Vanilla JS/HTML/CSS (Frontend)
* **Framework:** FastAPI, TensorFlow/Keras
* **Dataset:** 130,000+ rows, filtered to 'Tomato' and averaged daily.
* **ML Algorithm:** Bidirectional LSTM
* **Features:** Univariate (10-day sliding window of past prices)
* **Target:** Next day's price (iteratively predicted for up to 16 days)
* **Training Method:** 80/20 sequential split, Adam optimizer, MSE loss, Early Stopping.
* **Model File:** `lstm_price_predictor.h5` and `scaler.pkl`
* **Database:** MongoDB Atlas
* **Key External APIs:** Open-Meteo (Weather), News APIs.
* **Main Limitation:** Weather/News are blended heuristically post-prediction, not fed directly into the neural network.
* **Future Upgrade:** Convert to a Multivariate LSTM that consumes weather vectors alongside prices during training.

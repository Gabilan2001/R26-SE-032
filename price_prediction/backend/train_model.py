import os
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "datasets" / "Vegetables_fruit_prices_with_climate_130000_2020_to_2025.csv"
MODEL_DIR = BASE_DIR / "ml_models"

def main():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH, encoding='latin1')
    
    # Clean column names (handling any weird characters like the ? in C)
    df.columns = [col.replace("", "").strip() for col in df.columns]
    
    # Ensure Date column is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    print("Filtering for Tomato prices...")
    # Find the correct column name for vegitable_Commodity
    comm_col = [c for c in df.columns if 'vegitable_Commodity' in c][0]
    price_col = [c for c in df.columns if 'vegitable_Price' in c][0]
    
    df_tomato = df[df[comm_col].str.contains('Tomato', case=False, na=False)]
    
    if df_tomato.empty:
        print("Error: No Tomato data found in the dataset.")
        # fallback to using all veg data as mock
        df_tomato = df
    
    # Group by Date to get the daily average price across regions
    daily_avg = df_tomato.groupby('Date')[price_col].mean().reset_index()
    daily_avg = daily_avg.sort_values('Date')
    
    prices = daily_avg[price_col].values.reshape(-1, 1)
    
    print("Scaling data...")
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_prices = scaler.fit_transform(prices)
    
    window_size = 10
    X, y = [], []
    for i in range(window_size, len(scaled_prices)):
        X.append(scaled_prices[i-window_size:i, 0])
        y.append(scaled_prices[i, 0])
        
    X, y = np.array(X), np.array(y)
    
    # Reshape X to [samples, time steps, features]
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    # Split train/test (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print(f"Building model... Train shape: {X_train.shape}, Test shape: {X_test.shape}")
    model = Sequential([
        Bidirectional(LSTM(units=50, return_sequences=True), input_shape=(X_train.shape[1], 1)),
        Dropout(0.2),
        Bidirectional(LSTM(units=50, return_sequences=False)),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1)
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    
    # Callbacks
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.0001)
    
    print("Training model...")
    model.fit(
        X_train, y_train, 
        epochs=50, 
        batch_size=32, 
        validation_data=(X_test, y_test), 
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    print("Saving model and scaler...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_DIR / "lstm_price_predictor.h5")
    
    with open(MODEL_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
        
    print("Done! Model and scaler saved to ml_models/")

if __name__ == "__main__":
    main()

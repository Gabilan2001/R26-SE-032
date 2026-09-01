import os
import pickle
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
import pmdarima as pm
from statsmodels.tsa.arima.model import ARIMA
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.layers import GRU, LSTM, Bidirectional, Dense, Dropout
from tensorflow.keras.models import Sequential, load_model

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "datasets" / "tomato_prices_vegetablesSriLanka.csv"
MODEL_DIR = BASE_DIR / "ml_models"


def train_and_eval_series(
    df: pd.DataFrame,
    market: str,
    series_type: str,
    window_size: int = 10,
    model_dir: Path = MODEL_DIR,
    force_retrain: bool = False,
):
    series_label = f"{market}-{series_type}"
    file_suffix = f"{market.lower()}_{series_type.lower()}"
    print(f"\n==================================================")
    print(f" Processing Series: {series_label}")
    print(f"==================================================")

    # 1. Filter and sort series
    sub_df = df[(df["Market"] == market) & (df["Type"] == series_type)].copy()
    if sub_df.empty:
        raise ValueError(f"No data found for Market: {market}, Type: {series_type}")

    sub_df["Date"] = pd.to_datetime(sub_df["Date"])
    sub_df = sub_df.sort_values("Date").reset_index(drop=True)
    total_rows = len(sub_df)

    # 2. Missing/Malformed data handling & reporting
    raw_nan_count = sub_df["Price"].isna().sum()
    coerced_price = pd.to_numeric(sub_df["Price"], errors="coerce")
    total_na_after_coerce = coerced_price.isna().sum()
    malformed_count = total_na_after_coerce - raw_nan_count

    sub_df["Price"] = coerced_price

    print(f"Total rows: {total_rows}")
    print(f"Rows with source NaN values: {raw_nan_count}")
    print(f"Rows with failed numeric conversion (malformed): {malformed_count}")
    print(f"Total rows requiring interpolation: {total_na_after_coerce}")

    # Interpolation with limit_direction='both'
    interp_standard = sub_df["Price"].interpolate(method="linear")
    nan_rem_standard = interp_standard.isna().sum()

    if nan_rem_standard > 0:
        first_valid = interp_standard.first_valid_index()
        last_valid = interp_standard.last_valid_index()
        start_nans = first_valid if (first_valid is not None and first_valid > 0) else 0
        end_nans = (total_rows - 1 - last_valid) if (last_valid is not None and last_valid < total_rows - 1) else 0
        print(f"WARNING: Standard linear interpolation left {nan_rem_standard} NaNs (start edge: {start_nans}, end edge: {end_nans}).")
    else:
        print("Standard linear interpolation left 0 remaining NaNs.")

    sub_df["Price"] = sub_df["Price"].interpolate(method="linear", limit_direction="both")
    remaining_nans = sub_df["Price"].isna().sum()
    print(f"Final NaNs remaining after interpolation (limit_direction='both'): {remaining_nans}")

    if remaining_nans > 0:
        raise ValueError(f"Series for {series_label} still contains {remaining_nans} NaNs after interpolation!")

    # 3. Create sequence windows
    prices_1d = sub_df["Price"].values

    X_raw, y_raw = [], []
    for i in range(window_size, len(prices_1d)):
        X_raw.append(prices_1d[i - window_size : i])
        y_raw.append(prices_1d[i])

    X_raw, y_raw = np.array(X_raw), np.array(y_raw)

    # 80/20 train/test split
    split_idx = int(len(X_raw) * 0.8)
    X_train_raw, X_test_raw = X_raw[:split_idx], X_raw[split_idx:]
    y_train_raw, y_test_raw = y_raw[:split_idx], y_raw[split_idx:]

    # Scaler leakage fix: fit MinMaxScaler ONLY on 1D training prices
    scaler = MinMaxScaler(feature_range=(0, 1))
    train_prices_1d = prices_1d[: split_idx + window_size]
    scaler.fit(train_prices_1d.reshape(-1, 1))

    X_train_scaled = scaler.transform(X_train_raw.reshape(-1, 1)).reshape(X_train_raw.shape)
    X_test_scaled = scaler.transform(X_test_raw.reshape(-1, 1)).reshape(X_test_raw.shape)
    y_train_scaled = scaler.transform(y_train_raw.reshape(-1, 1)).flatten()

    X_train_3d = np.reshape(X_train_scaled, (X_train_scaled.shape[0], X_train_scaled.shape[1], 1))

    # Multi-Horizon Evaluation parameters
    horizons = [1, 3, 7, 14]
    max_horizon = max(horizons)
    valid_test_count = len(X_test_raw) - (max_horizon - 1)

    X_test_eval_raw = X_test_raw[:valid_test_count] # shape: (valid_test_count, 10)
    today_prices = X_test_eval_raw[:, -1]

    # Matrix of actual prices for each horizon h (shape: valid_test_count)
    actuals_by_horizon = {}
    for h in horizons:
        actuals_by_horizon[h] = np.array(
            [prices_1d[split_idx + window_size + i + h - 1] for i in range(valid_test_count)]
        )

    model_dir.mkdir(parents=True, exist_ok=True)
    series_eval_rows = []

    # ----------------------------------------------------
    # Model 1: Naive Baseline (Day t = Day t-1 price)
    # ----------------------------------------------------
    print(f"Evaluating Model 1/5: Naive Baseline...")
    for h in horizons:
        y_true = actuals_by_horizon[h]
        y_pred = today_prices
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        series_eval_rows.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Model": "Naive Baseline",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
        })
    print(f" -> Naive Baseline evaluation complete.")

    # ----------------------------------------------------
    # Model 2: Bidirectional LSTM
    # ----------------------------------------------------
    print(f"Processing Model 2/5: Bidirectional LSTM...")
    lstm_file = model_dir / f"lstm_{file_suffix}.h5"
    scaler_file = model_dir / f"scaler_{file_suffix}.pkl"

    # --- LEGACY RECURSIVE LSTM (PREVIOUS PRODUCTION - KEPT FOR ROLLBACK) ---
    # if not force_retrain and lstm_file.is_file() and scaler_file.is_file():
    #     print(f" Reusing existing LSTM model '{lstm_file.name}'...")
    #     lstm_model = load_model(lstm_file, compile=False)
    # else:
    #     lstm_model = Sequential([
    #         Bidirectional(LSTM(units=50, return_sequences=True), input_shape=(X_train_3d.shape[1], 1)),
    #         Dropout(0.2),
    #         Bidirectional(LSTM(units=50, return_sequences=False)),
    #         Dropout(0.2),
    #         Dense(units=25),
    #         Dense(units=1),
    #     ])
    #     lstm_model.compile(optimizer="adam", loss="mean_squared_error")
    #     early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    #     reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=0.0001)
    #
    #     y_test_scaled = scaler.transform(y_test_raw.reshape(-1, 1)).flatten()
    #     X_test_3d = np.reshape(X_test_scaled, (X_test_scaled.shape[0], X_test_scaled.shape[1], 1))
    #
    #     lstm_model.fit(
    #         X_train_3d,
    #         y_train_scaled,
    #         epochs=50,
    #         batch_size=32,
    #         validation_data=(X_test_3d, y_test_scaled),
    #         callbacks=[early_stop, reduce_lr],
    #         verbose=0,
    #     )
    #     lstm_model.save(lstm_file)
    #     with open(scaler_file, "wb") as f:
    #         pickle.dump(scaler, f)
    #
    # curr_windows_scaled = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_count, window_size, 1)
    # lstm_preds_matrix = np.zeros((valid_test_count, max_horizon))
    # for step in range(max_horizon):
    #     preds_scaled = lstm_model.predict(curr_windows_scaled, verbose=0)
    #     preds_real = scaler.inverse_transform(preds_scaled).flatten()
    #     lstm_preds_matrix[:, step] = preds_real
    #     curr_windows_scaled = np.concatenate([curr_windows_scaled[:, 1:, :], preds_scaled[:, np.newaxis, :]], axis=1)

    # --- DIRECT MULTI-OUTPUT BI-LSTM (NEW PRODUCTION - DENSE(14)) ---
    # Construct 14-day training targets strictly within training slice
    X_train_mimo_raw, Y_train_mimo_raw = [], []
    for orig_idx in range(window_size - 1, split_idx - max_horizon):
        X_train_mimo_raw.append(prices_1d[orig_idx - window_size + 1 : orig_idx + 1])
        Y_train_mimo_raw.append(prices_1d[orig_idx + 1 : orig_idx + max_horizon + 1])
    X_train_mimo_raw = np.array(X_train_mimo_raw)
    Y_train_mimo_raw = np.array(Y_train_mimo_raw)

    X_train_mimo_scaled = scaler.transform(X_train_mimo_raw.reshape(-1, 1)).reshape(len(X_train_mimo_raw), window_size, 1)
    Y_train_mimo_scaled = scaler.transform(Y_train_mimo_raw.reshape(-1, 1)).reshape(len(Y_train_mimo_raw), max_horizon)

    # Construct validation set for EarlyStopping
    X_val_mimo_raw, Y_val_mimo_raw = [], []
    for orig_idx in range(split_idx, len(prices_1d) - max_horizon):
        X_val_mimo_raw.append(prices_1d[orig_idx - window_size + 1 : orig_idx + 1])
        Y_val_mimo_raw.append(prices_1d[orig_idx + 1 : orig_idx + max_horizon + 1])
    X_val_mimo_raw = np.array(X_val_mimo_raw)
    Y_val_mimo_raw = np.array(Y_val_mimo_raw)

    X_val_mimo_scaled = scaler.transform(X_val_mimo_raw.reshape(-1, 1)).reshape(len(X_val_mimo_raw), window_size, 1)
    Y_val_mimo_scaled = scaler.transform(Y_val_mimo_raw.reshape(-1, 1)).reshape(len(Y_val_mimo_raw), max_horizon)

    if not force_retrain and lstm_file.is_file() and scaler_file.is_file():
        try:
            lstm_model = load_model(lstm_file, compile=False)
            if lstm_model.output_shape[-1] == max_horizon:
                print(f" Reusing existing Direct Multi-Output LSTM model '{lstm_file.name}'...")
            else:
                print(f" Existing LSTM model '{lstm_file.name}' has legacy output shape {lstm_model.output_shape[-1]}, retraining Direct MIMO ({max_horizon})...")
                lstm_model = None
        except Exception:
            lstm_model = None
    else:
        lstm_model = None

    if lstm_model is None:
        lstm_model = Sequential([
            Bidirectional(LSTM(units=50, return_sequences=True), input_shape=(window_size, 1)),
            Dropout(0.2),
            Bidirectional(LSTM(units=50, return_sequences=False)),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=max_horizon),
        ])
        lstm_model.compile(optimizer="adam", loss="mean_squared_error")
        early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=0.0001)

        lstm_model.fit(
            X_train_mimo_scaled,
            Y_train_mimo_scaled,
            epochs=50,
            batch_size=32,
            validation_data=(X_val_mimo_scaled, Y_val_mimo_scaled),
            callbacks=[early_stop, reduce_lr],
            verbose=0,
        )
        lstm_model.save(lstm_file)
        with open(scaler_file, "wb") as f:
            pickle.dump(scaler, f)

    curr_windows_scaled = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_count, window_size, 1)
    preds_scaled_mimo = lstm_model.predict(curr_windows_scaled, verbose=0)
    lstm_preds_matrix = scaler.inverse_transform(preds_scaled_mimo.reshape(-1, 1)).reshape(valid_test_count, max_horizon)

    for h in horizons:
        y_true = actuals_by_horizon[h]
        y_pred = lstm_preds_matrix[:, h - 1]
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        series_eval_rows.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Model": "Direct Multi-Output Bi-LSTM",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
        })
    print(f" -> Direct Multi-Output Bi-LSTM evaluation complete.")

    # ----------------------------------------------------
    # Model 3: Bidirectional GRU
    # ----------------------------------------------------
    print(f"Processing Model 3/5: Bidirectional GRU...")
    gru_file = model_dir / f"gru_{file_suffix}.h5"

    if not force_retrain and gru_file.is_file():
        print(f" Reusing existing GRU model '{gru_file.name}'...")
        gru_model = load_model(gru_file, compile=False)
    else:
        X_train_3d = np.reshape(X_train_raw, (X_train_raw.shape[0], X_train_raw.shape[1], 1))
        y_train_scaled = scaler.transform(y_train_raw.reshape(-1, 1)).flatten()
        X_test_3d = np.reshape(X_test_raw, (X_test_raw.shape[0], X_test_raw.shape[1], 1))
        y_test_scaled = scaler.transform(y_test_raw.reshape(-1, 1)).flatten()

        gru_model = Sequential([
            Bidirectional(GRU(units=50, return_sequences=True), input_shape=(window_size, 1)),
            Dropout(0.2),
            Bidirectional(GRU(units=50, return_sequences=False)),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1),
        ])
        gru_model.compile(optimizer="adam", loss="mean_squared_error")
        early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
        reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, min_lr=0.0001)

        gru_model.fit(
            X_train_3d,
            y_train_scaled,
            epochs=50,
            batch_size=32,
            validation_data=(X_test_3d, y_test_scaled),
            callbacks=[early_stop, reduce_lr],
            verbose=0,
        )
        gru_model.save(gru_file)

    curr_windows_scaled_gru = scaler.transform(X_test_eval_raw.reshape(-1, 1)).reshape(valid_test_count, window_size, 1)
    gru_preds_matrix = np.zeros((valid_test_count, max_horizon))
    for step in range(max_horizon):
        preds_scaled = gru_model.predict(curr_windows_scaled_gru, verbose=0)
        preds_real = scaler.inverse_transform(preds_scaled).flatten()
        gru_preds_matrix[:, step] = preds_real
        curr_windows_scaled_gru = np.concatenate([curr_windows_scaled_gru[:, 1:, :], preds_scaled[:, np.newaxis, :]], axis=1)

    for h in horizons:
        y_true = actuals_by_horizon[h]
        y_pred = gru_preds_matrix[:, h - 1]
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        series_eval_rows.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Model": "GRU",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
        })
    print(f" -> GRU evaluation complete.")

    # ----------------------------------------------------
    # Model 4: Random Forest Regressor
    # ----------------------------------------------------
    print(f"Processing Model 4/5: Random Forest...")
    rf_file = model_dir / f"rf_{file_suffix}.pkl"
    if not force_retrain and rf_file.is_file():
        print(f" Reusing existing Random Forest model '{rf_file.name}'...")
        with open(rf_file, "rb") as f:
            rf_model = pickle.load(f)
    else:
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_model.fit(X_train_raw, y_train_raw)
        with open(rf_file, "wb") as f:
            pickle.dump(rf_model, f)

    curr_windows_rf = X_test_eval_raw.copy()
    rf_preds_matrix = np.zeros((valid_test_count, max_horizon))
    for step in range(max_horizon):
        preds_step = rf_model.predict(curr_windows_rf)
        rf_preds_matrix[:, step] = preds_step
        curr_windows_rf = np.hstack([curr_windows_rf[:, 1:], preds_step.reshape(-1, 1)])

    for h in horizons:
        y_true = actuals_by_horizon[h]
        y_pred = rf_preds_matrix[:, h - 1]
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        series_eval_rows.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Model": "Random Forest",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
        })
    print(f" -> Random Forest evaluation complete.")

    # ----------------------------------------------------
    # Model 5: XGBoost Regressor
    # ----------------------------------------------------
    print(f"Processing Model 5/5: XGBoost...")
    xgb_file = model_dir / f"xgboost_{file_suffix}.pkl"
    if not force_retrain and xgb_file.is_file():
        print(f" Reusing existing XGBoost model '{xgb_file.name}'...")
        with open(xgb_file, "rb") as f:
            xgb_model = pickle.load(f)
    else:
        xgb_model = xgb.XGBRegressor(n_estimators=100, random_state=42)
        xgb_model.fit(X_train_raw, y_train_raw)
        with open(xgb_file, "wb") as f:
            pickle.dump(xgb_model, f)

    curr_windows_xgb = X_test_eval_raw.copy()
    xgb_preds_matrix = np.zeros((valid_test_count, max_horizon))
    for step in range(max_horizon):
        preds_step = xgb_model.predict(curr_windows_xgb)
        xgb_preds_matrix[:, step] = preds_step
        curr_windows_xgb = np.hstack([curr_windows_xgb[:, 1:], preds_step.reshape(-1, 1)])

    for h in horizons:
        y_true = actuals_by_horizon[h]
        y_pred = xgb_preds_matrix[:, h - 1]
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        series_eval_rows.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Model": "XGBoost",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
        })
    print(f" -> XGBoost evaluation complete.")

    # ----------------------------------------------------
    # Model 6: ARIMA (pmdarima auto_arima order selection)
    # ----------------------------------------------------
    print(f"Processing Model 6/5: ARIMA (pmdarima auto_arima)...")
    arima_file = model_dir / f"arima_{file_suffix}.pkl"

    if not force_retrain and arima_file.is_file():
        print(f" Reusing existing ARIMA model '{arima_file.name}'...")
        with open(arima_file, "rb") as f:
            arima_saved_info = pickle.load(f)
            order = arima_saved_info["order"]
            method_used = arima_saved_info["method"]
    else:
        print(f" Fitting auto_arima on raw training prices for {series_label}...")
        auto_fit = pm.auto_arima(
            train_prices_1d,
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
            max_p=5,
            max_q=5,
        )
        order = auto_fit.order
        method_used = "pmdarima auto_arima"
        arima_saved_info = {"order": order, "method": method_used}
        with open(arima_file, "wb") as f:
            pickle.dump(arima_saved_info, f)

    print(f" [{series_label}] ARIMA Method: {method_used} | Selected Order (p,d,q): {order}")

    # Fast multi-step evaluation for ARIMA using statsmodels ARIMA fitted with selected (p,d,q) order
    # Fit statsmodels ARIMA on train_prices_1d
    sm_arima_base = ARIMA(train_prices_1d, order=order).fit()
    
    # Evaluate across test samples strictly using historical data up to day t-1 (no target leakage)
    test_prices_1d = prices_1d[split_idx + window_size :]
    
    arima_preds_matrix = np.zeros((valid_test_count, max_horizon))
    for i in range(valid_test_count):
        if i == 0:
            sub_model = sm_arima_base
        else:
            sub_model = sm_arima_base.append(test_prices_1d[:i], refit=False)
        forecast_14 = sub_model.forecast(steps=max_horizon)
        arima_preds_matrix[i, :] = forecast_14

    for h in horizons:
        y_true = actuals_by_horizon[h]
        y_pred = arima_preds_matrix[:, h - 1]
        mae = np.mean(np.abs(y_true - y_pred))
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        series_eval_rows.append({
            "Series": series_label,
            "Horizon": f"{h}-day",
            "Model": "ARIMA",
            "MAE": mae,
            "RMSE": rmse,
            "MAPE": mape,
        })
    print(f" -> ARIMA evaluation complete.")

    return series_eval_rows


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate price prediction models")
    parser.add_argument("--force-retrain", action="store_true", default=False, help="Force retrain all models")
    args, _ = parser.parse_known_args()

    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Dataset file not found at: {DATA_PATH}")

    print(f"Loading dataset from: {DATA_PATH.name}...")
    df = pd.read_csv(DATA_PATH)
    df.columns = [col.strip() for col in df.columns]

    series_combinations = [
        ("Dambulla", "Retail"),
        ("Dambulla", "Wholesale"),
        ("Pettah", "Retail"),
        ("Pettah", "Wholesale"),
    ]

    all_eval_results = []
    for market, series_type in series_combinations:
        eval_rows = train_and_eval_series(df, market, series_type, window_size=10, force_retrain=args.force_retrain)
        all_eval_results.extend(eval_rows)

    # Format Summary Table
    summary_df = pd.DataFrame(all_eval_results)
    summary_df["MAE"] = summary_df["MAE"].apply(lambda x: f"{x:.2f}")
    summary_df["RMSE"] = summary_df["RMSE"].apply(lambda x: f"{x:.2f}")
    summary_df["MAPE"] = summary_df["MAPE"].apply(lambda x: f"{x:.2f}%")

    print("\n" + "=" * 76)
    print(" CONSOLIDATED MULTI-MODEL & MULTI-HORIZON EVALUATION SUMMARY TABLE")
    print("=" * 76)
    print(summary_df.to_string(index=False))
    print("=" * 76)


if __name__ == "__main__":
    main()

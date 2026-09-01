@echo off
REM Automated Daily Tomato Price Ingestion Script for Windows Task Scheduler
REM Navigates to price_prediction/backend and runs update_cbsl_prices.py

cd /d "%~dp0\.."
echo [%DATE% %TIME%] Starting daily price ingestion sync...
python scripts\update_cbsl_prices.py >> datasets\cbsl_scheduler_runs.log 2>&1
echo [%DATE% %TIME%] Price ingestion finished with exit code %ERRORLEVEL%.

#!/usr/bin/env bash
# Automated Daily Tomato Price Ingestion Script for Linux Cron Job
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[$(date -u)] Starting daily price ingestion sync..."
python3 scripts/update_cbsl_prices.py >> datasets/cbsl_scheduler_runs.log 2>&1
echo "[$(date -u)] Price ingestion completed."

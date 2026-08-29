"""
Automated CBSL Tomato Price Data Ingestion and Gap Filling Script.

Retrieves official CBSL Daily Price Reports, extracts tomato prices for:
- Dambulla Retail
- Dambulla Wholesale
- Pettah Retail
- Pettah Wholesale

Fills historical gaps, detects conflicts, prevents duplicates, and logs source provenance.

Usage:
  python backend/scripts/update_cbsl_prices.py --dry-run
  python backend/scripts/update_cbsl_prices.py
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import io
import logging
import os
from pathlib import Path
import re
import ssl
import sys
from typing import Any, Dict, List, Optional, Tuple
import urllib.request

import pandas as pd
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cbsl_ingestion")

# Paths relative to backend directory
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DATASETS_DIR = BACKEND_DIR / "datasets"
BACKUPS_DIR = DATASETS_DIR / "backups"
PRICE_CSV_PATH = DATASETS_DIR / "tomato_prices_vegetablesSriLanka.csv"
INGESTION_LOG_PATH = DATASETS_DIR / "cbsl_ingestion_log.csv"

# Target Series Definitions
SERIES_MAP = {
    "Pettah_Wholesale": ("Pettah", "Wholesale", 1),
    "Dambulla_Wholesale": ("Dambulla", "Wholesale", 3),
    "Pettah_Retail": ("Pettah", "Retail", 5),
    "Dambulla_Retail": ("Dambulla", "Retail", 7),
}


def get_ssl_context() -> ssl.SSLContext:
    """Create SSL context that bypasses certificate verification for CBSL endpoints."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_cbsl_pdf_for_date(curr_dt: datetime) -> Tuple[datetime, str, Optional[bytes], Optional[str]]:
    """
    Attempt to fetch CBSL Daily Price Report PDF for a specific date.
    Returns: (curr_dt, dt_formatted, pdf_bytes, report_url)
    """
    dt_str = curr_dt.strftime("%Y%m%d")
    dt_formatted = curr_dt.strftime("%Y-%m-%d")

    pattern_urls = [
        f"https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/pricerpt/price_report_{dt_str}_e.pdf",
        f"https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/statistics/pricerpt/price_report_{dt_str}e.pdf",
    ]
    ctx = get_ssl_context()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for url in pattern_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                if resp.status == 200:
                    content = resp.read()
                    if content.startswith(b"%PDF") and len(content) > 1000:
                        return curr_dt, dt_formatted, content, url
        except Exception:
            continue
    return curr_dt, dt_formatted, None, None


def extract_tomato_prices_from_pdf(pdf_bytes: bytes) -> Optional[Dict[str, float]]:
    """
    Extract Tomato prices from CBSL Daily Price Report PDF content.
    Returns dict mapping: {"Pettah_Wholesale": price, "Dambulla_Wholesale": price, ...}
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if len(reader.pages) < 2:
            return None

        page2_text = reader.pages[1].extract_text()
        tomato_line = None
        for line in page2_text.split("\n"):
            if "Tomato" in line:
                tomato_line = line
                break

        if not tomato_line:
            return None

        tokens = re.findall(r"(\d+(?:\.\d+)?|n\.a\.)", tomato_line)
        if len(tokens) < 8:
            return None

        extracted = {}
        for key, (market, series_type, token_idx) in SERIES_MAP.items():
            val_str = tokens[token_idx]
            if val_str != "n.a.":
                try:
                    price = float(val_str)
                    if price > 0:
                        extracted[key] = price
                except ValueError:
                    pass

        return extracted if extracted else None
    except Exception as e:
        logger.debug("PDF parsing error: %s", e)
        return None


def create_dataset_backup() -> Path:
    """Create timestamped backup of existing tomato_prices_vegetablesSriLanka.csv."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"tomato_prices_vegetablesSriLanka_backup_{timestamp}.csv"
    backup_path = BACKUPS_DIR / backup_filename

    if PRICE_CSV_PATH.is_file():
        import shutil
        shutil.copy2(PRICE_CSV_PATH, backup_path)
        logger.info("Created backup at: %s", backup_path)
    return backup_path


def load_existing_dataset() -> pd.DataFrame:
    """Load existing dataset and return DataFrame with standardized columns."""
    if not PRICE_CSV_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found at {PRICE_CSV_PATH}")

    df = pd.read_csv(PRICE_CSV_PATH)
    df.columns = [c.strip() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    return df


def run_ingestion_pipeline(dry_run: bool = False, full_gap_rescan: bool = False):
    """Execute CBSL data ingestion, gap recovery, duplicate/conflict check, and update."""
    logger.info("=== CBSL Tomato Price Ingestion Pipeline ===")
    logger.info("Dataset Path: %s", PRICE_CSV_PATH)

    df_existing = load_existing_dataset()
    existing_records_count = len(df_existing)

    existing_map = {}
    for _, row in df_existing.iterrows():
        key = (str(row["Date"]), str(row["Item"]), str(row["Type"]), str(row["Market"]))
        existing_map[key] = float(row["Price"])

    df_existing["Date_dt"] = pd.to_datetime(df_existing["Date"])
    min_date = df_existing["Date_dt"].min().strftime("%Y-%m-%d")
    max_date = df_existing["Date_dt"].max().strftime("%Y-%m-%d")

    scan_end = datetime.now() + timedelta(days=1)
    if full_gap_rescan:
        scan_start = datetime(2026, 3, 11)
    else:
        last_dt = df_existing["Date_dt"].max()
        scan_start = max(datetime(2026, 3, 11), last_dt + timedelta(days=1))

    logger.info("Existing Tomato Records: %d", existing_records_count)
    logger.info("Earliest Date in Dataset: %s", min_date)
    logger.info("Latest Date in Dataset: %s", max_date)

    if scan_start > scan_end:
        print("\nNo new CBSL report available. Dataset unchanged.")
        return

    logger.info("Scanning CBSL Reports for range: %s to %s...", scan_start.strftime("%Y-%m-%d"), scan_end.strftime("%Y-%m-%d"))

    dates_to_scan = []
    curr_dt = scan_start
    while curr_dt <= scan_end:
        if full_gap_rescan or curr_dt.weekday() < 5:
            dates_to_scan.append(curr_dt)
        curr_dt += timedelta(days=1)

    if not dates_to_scan:
        print("\nNo new CBSL report available. Dataset unchanged.")
        return

    fetch_results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(fetch_cbsl_pdf_for_date, dt) for dt in dates_to_scan]
        for f in as_completed(futures):
            fetch_results.append(f.result())

    fetch_results.sort(key=lambda x: x[0])

    cbsl_reports_found = 0
    cbsl_reports_unavailable = 0
    new_records: List[Dict[str, Any]] = []
    log_records: List[Dict[str, Any]] = []
    duplicates_count = 0
    conflicts: List[Dict[str, Any]] = []
    recovered_dates = set()
    retrieved_at_str = datetime.now(timezone.utc).isoformat()

    for _, dt_formatted, pdf_bytes, report_url in fetch_results:
        if pdf_bytes and report_url:
            cbsl_reports_found += 1
            extracted_prices = extract_tomato_prices_from_pdf(pdf_bytes)

            if extracted_prices:
                recovered_dates.add(dt_formatted)
                for key, price in extracted_prices.items():
                    market, series_type, _ = SERIES_MAP[key]
                    record_key = (dt_formatted, "Tomato", series_type, market)

                    if record_key in existing_map:
                        existing_price = existing_map[record_key]
                        if abs(existing_price - price) < 1e-3:
                            duplicates_count += 1
                        else:
                            conflicts.append({
                                "Date": dt_formatted,
                                "Market": market,
                                "Type": series_type,
                                "Existing_Price": existing_price,
                                "CBSL_Price": price,
                                "Report_URL": report_url,
                            })
                    else:
                        new_records.append({
                            "Date": dt_formatted,
                            "Item": "Tomato",
                            "Type": series_type,
                            "Market": market,
                            "Price": round(price, 2),
                        })
                        log_records.append({
                            "Date": dt_formatted,
                            "Item": "Tomato",
                            "Type": series_type,
                            "Market": market,
                            "Price": round(price, 2),
                            "Source": "CBSL Daily Price Report",
                            "Report_URL": report_url,
                            "Retrieved_At": retrieved_at_str,
                        })
        else:
            cbsl_reports_unavailable += 1

    print("\n" + "=" * 70)
    print(" INGESTION PIPELINE REPORT SUMMARY")
    print("=" * 70)
    print(f"Dataset Path: {PRICE_CSV_PATH}")
    print(f"Existing Tomato Records: {existing_records_count}")
    print(f"Earliest Tomato Date: {min_date}")
    print(f"Latest Tomato Date: {max_date}")
    print(f"Historical Gap Scanned: {scan_start.strftime('%Y-%m-%d')} -> {scan_end.strftime('%Y-%m-%d')}")
    print(f"CBSL Reports Found: {cbsl_reports_found}")
    print(f"Reports Unavailable (Holidays/No PDF): {cbsl_reports_unavailable}")
    print(f"Dates Recovered: {len(recovered_dates)}")
    print(f"New Records to Add: {len(new_records)}")
    print(f"Duplicates Skipped: {duplicates_count}")
    print(f"Conflicts Detected: {len(conflicts)}")
    print("=" * 70)

    if conflicts:
        print("\n--- CONFLICT DETAILS ---")
        for c in conflicts:
            print(f"Conflict on {c['Date']} [{c['Market']} {c['Type']}]: Existing CSV={c['Existing_Price']}, CBSL={c['CBSL_Price']} (URL: {c['Report_URL']})")
        print("Note: Preserved existing CSV values until explicitly approved.")

    if dry_run:
        print("\n[DRY-RUN MODE] No files were modified.")
        return

    if not new_records:
        print("\nNo new CBSL report available. Dataset unchanged.")
        return

    create_dataset_backup()

    df_new = pd.DataFrame(new_records)
    df_combined = pd.concat([df_existing.drop(columns=["Date_dt"], errors="ignore"), df_new], ignore_index=True)

    df_combined["Date_dt"] = pd.to_datetime(df_combined["Date"])
    df_combined = df_combined.sort_values(["Date_dt", "Market", "Type"]).drop(columns=["Date_dt"]).reset_index(drop=True)

    df_combined.to_csv(PRICE_CSV_PATH, index=False)
    logger.info("Successfully updated dataset at %s (Total rows: %d)", PRICE_CSV_PATH, len(df_combined))

    if log_records:
        df_log_new = pd.DataFrame(log_records)
        if INGESTION_LOG_PATH.is_file():
            df_log_old = pd.read_csv(INGESTION_LOG_PATH)
            df_log_combined = pd.concat([df_log_old, df_log_new], ignore_index=True)
        else:
            df_log_combined = df_log_new
        df_log_combined.to_csv(INGESTION_LOG_PATH, index=False)
        logger.info("Saved provenance log to %s (%d total log entries)", INGESTION_LOG_PATH, len(df_log_combined))

    print("\nDataset update complete!")


def main():
    parser = argparse.ArgumentParser(description="CBSL Tomato Price Ingestion Script")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry-run inspection without modifying files")
    parser.add_argument("--full-rescan", action="store_true", help="Perform full rescan of historical gap starting from 2026-03-11")
    args = parser.parse_args()

    run_ingestion_pipeline(dry_run=args.dry_run, full_gap_rescan=args.full_rescan)


if __name__ == "__main__":
    main()

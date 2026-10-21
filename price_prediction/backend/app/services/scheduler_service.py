"""
Automated Background Scheduler for Daily Market Price Ingestion.

Executes periodic background checks for new CBSL and HARTI daily price bulletins
at configured times (e.g. 06:30 and 16:30 Asia/Colombo time) and on application startup.
Runs gracefully as an async background task within the FastAPI lifespan.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
import sys
from typing import Optional

logger = logging.getLogger("price_scheduler")

_scheduler_task: Optional[asyncio.Task] = None
_stop_event: asyncio.Event = asyncio.Event()


def trigger_cbsl_ingestion_sync() -> dict:
    """Synchronously execute CBSL ingestion pipeline from update_cbsl_prices script."""
    try:
        from scripts.update_cbsl_prices import run_ingestion_pipeline, load_existing_dataset
        logger.info("Executing scheduled CBSL price ingestion...")
        run_ingestion_pipeline(dry_run=False, full_gap_rescan=False)
        df = load_existing_dataset()
        return {
            "status": "success",
            "latest_date": str(df["Date"].max()),
            "total_records": len(df),
        }
    except Exception as exc:
        logger.error("Error during scheduled CBSL price ingestion: %s", exc)
        return {
            "status": "error",
            "error": str(exc),
        }


async def _scheduler_loop():
    """Background loop checking hourly and triggering at 06:30 and 16:30 SLT (UTC+5:30)."""
    logger.info("Price Ingestion Background Scheduler started.")
    
    # Run an initial non-blocking sync 10 seconds after startup
    await asyncio.sleep(10)
    if not _stop_event.is_set():
        logger.info("Running startup price ingestion check...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, trigger_cbsl_ingestion_sync)

    last_run_hour = -1

    while not _stop_event.is_set():
        try:
            # Check current time in Sri Lanka (UTC + 5:30)
            now_utc = datetime.now(timezone.utc)
            # Offset for Asia/Colombo (UTC+5:30)
            sl_hour = (now_utc.hour + 5 + (now_utc.minute + 30) // 60) % 24
            sl_minute = (now_utc.minute + 30) % 60

            # Target run hours: 6 AM (after morning bulletin) and 16 (4 PM after afternoon DEC updates)
            if sl_hour in (6, 16) and sl_hour != last_run_hour:
                logger.info("Scheduled trigger hit (Hour: %d:00 SLT). Initiating price sync...", sl_hour)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, trigger_cbsl_ingestion_sync)
                last_run_hour = sl_hour

            # Sleep for 15 minutes before checking again
            await asyncio.sleep(900)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.warning("Scheduler loop encountered error: %s. Retrying in 5 minutes...", exc)
            await asyncio.sleep(300)

    logger.info("Price Ingestion Background Scheduler stopped.")


def start_scheduler():
    """Start background price ingestion task."""
    global _scheduler_task, _stop_event
    _stop_event.clear()
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())


def stop_scheduler():
    """Stop background price ingestion task."""
    global _scheduler_task, _stop_event
    _stop_event.set()
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()

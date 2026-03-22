"""
APScheduler setup — runs a daily refresh job inside the FastAPI process.
Uses the lifespan pattern (FastAPI 0.95+) for clean startup/shutdown.
"""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from database import SessionLocal
from services.schedule import refresh_current_week

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_refresh():
    """Job function — opens its own DB session (scheduler runs in a thread)."""
    logger.info("Scheduler: starting daily pitcher refresh")
    db = SessionLocal()
    try:
        refresh_current_week(db)
        logger.info("Scheduler: daily pitcher refresh complete")
    except Exception as e:
        logger.error(f"Scheduler: refresh failed — {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan — start scheduler on boot, stop on shutdown."""
    scheduler.add_job(
        _run_refresh,
        trigger="cron",
        hour=settings.refresh_hour,
        minute=settings.refresh_minute,
        id="daily_pitcher_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        f"Scheduler started — daily refresh at "
        f"{settings.refresh_hour:02d}:{settings.refresh_minute:02d} UTC"
    )
    yield
    scheduler.shutdown()
    logger.info("Scheduler stopped")

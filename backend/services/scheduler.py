from apscheduler.schedulers.background import BackgroundScheduler
from ..database import SessionLocal
from ..models import Platform
from .review_service import sync_platform_reviews
import logging

logger = logging.getLogger(__name__)

def scheduled_sync():
    logger.info("Starting scheduled review sync")
    db = SessionLocal()
    try:
        platforms = db.query(Platform).all()
        for platform in platforms:
            try:
                count = sync_platform_reviews(db, platform.id)
                logger.info(f"Synced {count} new reviews for {platform.name}")
            except Exception as e:
                logger.error(f"Error syncing {platform.name}: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run sync every 6 hours
    scheduler.add_job(scheduled_sync, 'interval', hours=6)
    scheduler.start()
    logger.info("Review sync scheduler started")

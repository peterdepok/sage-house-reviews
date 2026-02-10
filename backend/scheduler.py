"""
APScheduler configuration for periodic sync jobs.
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import settings


logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: BackgroundScheduler = None


def sync_job():
    """
    Periodic sync job - fetches reviews from all platforms.
    """
    from services.sync import run_sync
    from routers.health import set_scheduler_status
    
    logger.info("Starting scheduled sync job")
    
    try:
        result = run_sync()
        set_scheduler_status(True, datetime.utcnow())
        logger.info(
            f"Scheduled sync completed: "
            f"{result.get('total_new_reviews', 0)} new, "
            f"{result.get('total_updated_reviews', 0)} updated"
        )
    except Exception as e:
        logger.exception(f"Scheduled sync failed: {e}")


def weekly_digest_job():
    """
    Weekly digest job - sends summary email.
    """
    from services.notifications import WeeklyDigestService
    from database import get_db_context
    
    logger.info("Generating weekly digest")
    
    try:
        with get_db_context() as db:
            service = WeeklyDigestService(db)
            service.send_digest()
        logger.info("Weekly digest sent")
    except Exception as e:
        logger.exception(f"Weekly digest failed: {e}")


def rating_check_job():
    """
    Check for rating drops across platforms.
    """
    from services.alerts import AlertService
    from database import get_db_context
    from models import Platform
    
    logger.info("Checking for rating drops")
    
    try:
        with get_db_context() as db:
            service = AlertService(db)
            platforms = db.query(Platform).filter(Platform.is_active == True).all()
            
            for platform in platforms:
                service.check_rating_drop(platform.id)
        
        logger.info("Rating check completed")
    except Exception as e:
        logger.exception(f"Rating check failed: {e}")


def init_scheduler() -> BackgroundScheduler:
    """
    Initialize and configure the scheduler.
    
    Returns:
        Configured scheduler (not started)
    """
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = BackgroundScheduler(
        timezone="UTC",
        job_defaults={
            "coalesce": True,  # Combine missed runs into one
            "max_instances": 1,  # Only one instance of each job
            "misfire_grace_time": 300,  # 5 minute grace period
        }
    )
    
    # Add sync job - runs every N hours
    scheduler.add_job(
        sync_job,
        trigger=IntervalTrigger(hours=settings.SYNC_INTERVAL_HOURS),
        id="review_sync",
        name="Review Sync",
        replace_existing=True,
    )
    
    # Add weekly digest - runs every Monday at 9 AM UTC
    scheduler.add_job(
        weekly_digest_job,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_digest",
        name="Weekly Digest",
        replace_existing=True,
    )
    
    # Add rating check - runs daily at 8 AM UTC
    scheduler.add_job(
        rating_check_job,
        trigger=CronTrigger(hour=8, minute=0),
        id="rating_check",
        name="Rating Check",
        replace_existing=True,
    )
    
    logger.info("Scheduler initialized with jobs")
    
    return scheduler


def start_scheduler():
    """Start the scheduler if enabled."""
    global scheduler
    
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled in settings")
        return
    
    if scheduler is None:
        scheduler = init_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")
        
        # Update health status
        from routers.health import set_scheduler_status
        set_scheduler_status(True)


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")
        
        from routers.health import set_scheduler_status
        set_scheduler_status(False)


def get_scheduler_status() -> dict:
    """Get current scheduler status and job info."""
    global scheduler
    
    if scheduler is None:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs,
    }

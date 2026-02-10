"""
Health check and status endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db
from config import settings
from schemas import HealthCheck


router = APIRouter(tags=["health"])


# Track scheduler status
_scheduler_status = {"running": False, "last_run": None}


def set_scheduler_status(running: bool, last_run: datetime = None):
    """Called by scheduler to update status."""
    _scheduler_status["running"] = running
    if last_run:
        _scheduler_status["last_run"] = last_run


@router.get("/api/health", response_model=HealthCheck)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers.
    """
    # Check database connection
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check scheduler status
    scheduler_status = "running" if _scheduler_status["running"] else "stopped"
    if not settings.ENABLE_SCHEDULER:
        scheduler_status = "disabled"
    
    return HealthCheck(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        scheduler=scheduler_status,
        timestamp=datetime.utcnow(),
    )


@router.get("/api/status")
def detailed_status(db: Session = Depends(get_db)):
    """
    Detailed status endpoint with more information.
    """
    from models import Platform, Review, Alert, AlertStatus
    
    # Get counts
    platform_count = db.query(Platform).count()
    active_platforms = db.query(Platform).filter(Platform.is_active == True).count()
    review_count = db.query(Review).count()
    pending_alerts = db.query(Alert).filter(
        Alert.status == AlertStatus.PENDING
    ).count()
    
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "database": {
            "url": settings.DATABASE_URL.split("://")[0] + "://***",  # Hide credentials
            "platforms": platform_count,
            "active_platforms": active_platforms,
            "reviews": review_count,
            "pending_alerts": pending_alerts,
        },
        "scheduler": {
            "enabled": settings.ENABLE_SCHEDULER,
            "running": _scheduler_status["running"],
            "interval_hours": settings.SYNC_INTERVAL_HOURS,
            "last_run": _scheduler_status["last_run"].isoformat() if _scheduler_status["last_run"] else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/")
def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }

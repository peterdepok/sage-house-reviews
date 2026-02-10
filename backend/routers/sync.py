"""
API routes for sync operations.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from schemas import SyncRequest, SyncResponse, SyncResult
from services.sync import SyncService


router = APIRouter(prefix="/api/sync", tags=["sync"])


# Track background sync status
_sync_status = {
    "is_running": False,
    "last_sync": None,
    "last_result": None,
}


@router.post("", response_model=dict)
def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    wait: bool = False,
):
    """
    Trigger a sync operation.
    
    By default, runs in the background. Set wait=True to wait for completion.
    """
    if _sync_status["is_running"]:
        return {
            "message": "Sync already in progress",
            "status": "running",
        }
    
    if wait:
        # Synchronous sync
        service = SyncService(db)
        
        if request.platform_ids:
            result = service.sync_platforms_by_ids(request.platform_ids)
        else:
            result = service.sync_all_platforms()
        
        _sync_status["last_sync"] = datetime.utcnow()
        _sync_status["last_result"] = result
        
        return {
            "message": "Sync completed",
            "status": "completed",
            "result": result,
        }
    
    # Background sync
    _sync_status["is_running"] = True
    
    def run_background_sync():
        from database import get_db_context
        
        try:
            with get_db_context() as session:
                service = SyncService(session)
                
                if request.platform_ids:
                    result = service.sync_platforms_by_ids(request.platform_ids)
                else:
                    result = service.sync_all_platforms()
                
                _sync_status["last_sync"] = datetime.utcnow()
                _sync_status["last_result"] = result
        finally:
            _sync_status["is_running"] = False
    
    background_tasks.add_task(run_background_sync)
    
    return {
        "message": "Sync started",
        "status": "started",
    }


@router.get("/status")
def get_sync_status():
    """
    Get the current sync status.
    """
    return {
        "is_running": _sync_status["is_running"],
        "last_sync": _sync_status["last_sync"].isoformat() if _sync_status["last_sync"] else None,
        "last_result": _sync_status["last_result"],
    }


@router.post("/platform/{platform_id}")
def sync_single_platform(
    platform_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    wait: bool = False,
):
    """
    Sync a single platform.
    """
    from models import Platform
    
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    
    if not platform:
        return {"error": "Platform not found", "status": "error"}
    
    if wait:
        service = SyncService(db)
        result = service.sync_platform(platform)
        return {
            "message": f"Sync completed for {platform.name}",
            "status": "completed",
            "result": result,
        }
    
    def run_platform_sync():
        from database import get_db_context
        
        with get_db_context() as session:
            platform = session.query(Platform).filter(Platform.id == platform_id).first()
            if platform:
                service = SyncService(session)
                service.sync_platform(platform)
    
    background_tasks.add_task(run_platform_sync)
    
    return {
        "message": f"Sync started for {platform.name}",
        "status": "started",
    }

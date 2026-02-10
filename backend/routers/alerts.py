"""
API routes for alert management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, AlertStatus, AlertType
from schemas import AlertResponse, AlertUpdate
from services.alerts import AlertService


router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    alert_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get alerts with optional filtering.
    """
    service = AlertService(db)
    
    # Convert string to enum if provided
    status_enum = AlertStatus(status) if status else None
    type_enum = AlertType(alert_type) if alert_type else None
    
    alerts = service.get_alerts(
        status=status_enum,
        alert_type=type_enum,
        limit=limit,
        offset=offset,
    )
    
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/counts")
def get_alert_counts(db: Session = Depends(get_db)):
    """
    Get alert counts by status.
    """
    service = AlertService(db)
    return service.get_alert_counts()


@router.get("/pending", response_model=List[AlertResponse])
def get_pending_alerts(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get pending alerts that need attention.
    """
    service = AlertService(db)
    alerts = service.get_pending_alerts(limit=limit)
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Get a single alert by ID.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Mark an alert as acknowledged.
    """
    service = AlertService(db)
    alert = service.acknowledge_alert(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Mark an alert as resolved.
    """
    service = AlertService(db)
    alert = service.resolve_alert(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.post("/{alert_id}/dismiss", response_model=AlertResponse)
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    """
    Dismiss an alert.
    """
    service = AlertService(db)
    alert = service.dismiss_alert(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    update: AlertUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an alert's status.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if update.status:
        service = AlertService(db)
        
        if update.status == AlertStatus.ACKNOWLEDGED:
            alert = service.acknowledge_alert(alert_id)
        elif update.status == AlertStatus.RESOLVED:
            alert = service.resolve_alert(alert_id)
        elif update.status == AlertStatus.DISMISSED:
            alert = service.dismiss_alert(alert_id)
        else:
            alert.status = update.status
            db.commit()
    
    return AlertResponse.model_validate(alert)


@router.post("/bulk-update")
def bulk_update_alerts(
    alert_ids: List[int],
    status: AlertStatus,
    db: Session = Depends(get_db),
):
    """
    Update status for multiple alerts.
    """
    service = AlertService(db)
    count = service.bulk_update_status(alert_ids, status)
    
    return {
        "message": f"Updated {count} alerts",
        "updated_count": count,
    }

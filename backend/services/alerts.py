"""
Alert management service.
Handles creation, tracking, and resolution of review alerts.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Alert, AlertType, AlertStatus, Review, Platform


logger = logging.getLogger(__name__)


class AlertService:
    """
    Service for managing review alerts.
    
    Alerts are generated for:
    - Negative reviews (rating <= 2)
    - Reviews with very negative sentiment
    - Reviews needing response
    - Significant rating drops (when detected)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_alert(
        self,
        review_id: Optional[int],
        alert_type: AlertType,
        title: str,
        message: Optional[str] = None,
        severity: str = "medium",
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            review_id: Associated review ID (optional)
            alert_type: Type of alert
            title: Alert title
            message: Detailed message
            severity: low, medium, or high
            
        Returns:
            Created alert
        """
        # Check for duplicate active alerts
        existing = self.db.query(Alert).filter(
            Alert.review_id == review_id,
            Alert.alert_type == alert_type,
            Alert.status.in_([AlertStatus.PENDING, AlertStatus.ACKNOWLEDGED])
        ).first()
        
        if existing:
            logger.debug(f"Alert already exists for review {review_id}")
            return existing
        
        alert = Alert(
            review_id=review_id,
            alert_type=alert_type,
            title=title,
            message=message,
            severity=severity,
            status=AlertStatus.PENDING,
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.info(f"Created alert: {alert_type.value} - {title}")
        
        # Trigger notification (stub)
        self._send_notification(alert)
        
        return alert
    
    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        alert_type: Optional[AlertType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            status: Filter by status
            alert_type: Filter by type
            limit: Maximum results
            offset: Results offset
            
        Returns:
            List of alerts
        """
        query = self.db.query(Alert)
        
        if status:
            query = query.filter(Alert.status == status)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_pending_alerts(self, limit: int = 50) -> List[Alert]:
        """Get pending alerts that need attention."""
        return self.get_alerts(status=AlertStatus.PENDING, limit=limit)
    
    def get_alert_counts(self) -> Dict[str, int]:
        """Get counts of alerts by status."""
        counts = self.db.query(
            Alert.status,
            func.count(Alert.id)
        ).group_by(Alert.status).all()
        
        return {status.value: count for status, count in counts}
    
    def acknowledge_alert(self, alert_id: int) -> Optional[Alert]:
        """
        Mark an alert as acknowledged.
        
        Args:
            alert_id: ID of alert to acknowledge
            
        Returns:
            Updated alert or None if not found
        """
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def resolve_alert(self, alert_id: int) -> Optional[Alert]:
        """
        Mark an alert as resolved.
        
        Args:
            alert_id: ID of alert to resolve
            
        Returns:
            Updated alert or None if not found
        """
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def dismiss_alert(self, alert_id: int) -> Optional[Alert]:
        """
        Dismiss an alert without resolving.
        
        Args:
            alert_id: ID of alert to dismiss
            
        Returns:
            Updated alert or None if not found
        """
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not alert:
            return None
        
        alert.status = AlertStatus.DISMISSED
        alert.resolved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def bulk_update_status(
        self, 
        alert_ids: List[int], 
        new_status: AlertStatus
    ) -> int:
        """
        Update status for multiple alerts.
        
        Args:
            alert_ids: List of alert IDs
            new_status: New status to set
            
        Returns:
            Number of alerts updated
        """
        now = datetime.utcnow()
        update_data = {"status": new_status}
        
        if new_status == AlertStatus.ACKNOWLEDGED:
            update_data["acknowledged_at"] = now
        elif new_status in (AlertStatus.RESOLVED, AlertStatus.DISMISSED):
            update_data["resolved_at"] = now
        
        count = self.db.query(Alert).filter(
            Alert.id.in_(alert_ids)
        ).update(update_data, synchronize_session=False)
        
        self.db.commit()
        
        return count
    
    def check_rating_drop(self, platform_id: int, threshold: float = 0.3) -> bool:
        """
        Check if a platform has experienced a significant rating drop.
        
        Args:
            platform_id: Platform to check
            threshold: Rating drop threshold (default 0.3 stars)
            
        Returns:
            True if significant drop detected
        """
        from models import ReviewSnapshot
        
        # Get last two snapshots
        snapshots = self.db.query(ReviewSnapshot).filter(
            ReviewSnapshot.platform_id == platform_id
        ).order_by(
            ReviewSnapshot.snapshot_date.desc()
        ).limit(2).all()
        
        if len(snapshots) < 2:
            return False
        
        current = snapshots[0].average_rating
        previous = snapshots[1].average_rating
        
        if current is None or previous is None:
            return False
        
        drop = previous - current
        
        if drop >= threshold:
            logger.warning(
                f"Rating drop detected for platform {platform_id}: "
                f"{previous:.2f} -> {current:.2f}"
            )
            
            platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
            platform_name = platform.name if platform else f"Platform {platform_id}"
            
            self.create_alert(
                review_id=None,
                alert_type=AlertType.RATING_DROP,
                title=f"Rating Drop on {platform_name}",
                message=f"Rating dropped from {previous:.1f} to {current:.1f}",
                severity="high" if drop >= 0.5 else "medium",
            )
            
            return True
        
        return False
    
    def _send_notification(self, alert: Alert):
        """
        Send notification for new alert.
        
        STUB: Integrates with NotificationService.
        """
        from services.notifications import NotificationService, NotificationPayload
        
        try:
            service = NotificationService()
            
            # Get review details if available
            review_data = {}
            if alert.review_id:
                review = self.db.query(Review).filter(Review.id == alert.review_id).first()
                if review:
                    platform = self.db.query(Platform).filter(
                        Platform.id == review.platform_id
                    ).first()
                    review_data = {
                        "review_id": review.id,
                        "platform_name": platform.name if platform else "Unknown",
                        "rating": review.rating,
                        "reviewer_name": review.reviewer_name,
                        "review_text": review.review_text,
                    }
            
            payload = NotificationPayload(
                title=alert.title,
                message=alert.message or "",
                severity=alert.severity,
                data={"alert_id": alert.id, "review": review_data},
            )
            
            service.notify(payload)
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

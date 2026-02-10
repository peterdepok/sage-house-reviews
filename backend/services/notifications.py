"""
Notification service for sending alerts via email and webhooks.
Currently implemented as stubs for future integration.
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import json

from config import settings


logger = logging.getLogger(__name__)


@dataclass
class NotificationPayload:
    """Standard notification payload."""
    title: str
    message: str
    severity: str = "info"
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


class NotificationService:
    """
    Service for sending notifications via various channels.
    
    Supported channels (stubs):
    - Email (SMTP)
    - Webhook (HTTP POST)
    - Slack (future)
    - SMS (future)
    """
    
    def __init__(self):
        self.email_configured = bool(settings.SMTP_HOST and settings.SMTP_USER)
        self.webhook_configured = bool(settings.WEBHOOK_URL)
    
    def notify(
        self, 
        payload: NotificationPayload,
        channels: Optional[List[str]] = None
    ):
        """
        Send notification to specified channels.
        
        Args:
            payload: Notification content
            channels: List of channels ('email', 'webhook'). None = all configured
        """
        if channels is None:
            channels = []
            if self.email_configured:
                channels.append("email")
            if self.webhook_configured:
                channels.append("webhook")
        
        for channel in channels:
            try:
                if channel == "email":
                    self._send_email(payload)
                elif channel == "webhook":
                    self._send_webhook(payload)
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
    
    def _send_email(self, payload: NotificationPayload):
        """
        Send notification via email.
        
        STUB: Implement with smtplib when email is configured.
        """
        if not self.email_configured:
            logger.debug("Email notifications not configured, skipping")
            return
        
        logger.info(f"STUB: Would send email notification: {payload.title}")
        
        # TODO: Implement actual email sending
        # import smtplib
        # from email.mime.text import MIMEText
        # from email.mime.multipart import MIMEMultipart
        #
        # msg = MIMEMultipart()
        # msg['From'] = settings.SMTP_USER
        # msg['To'] = settings.NOTIFICATION_EMAIL
        # msg['Subject'] = f"[Sage House Reviews] {payload.title}"
        #
        # body = self._format_email_body(payload)
        # msg.attach(MIMEText(body, 'html'))
        #
        # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        #     server.send_message(msg)
    
    def _send_webhook(self, payload: NotificationPayload):
        """
        Send notification via webhook.
        
        STUB: Implement with requests when webhook URL is configured.
        """
        if not self.webhook_configured:
            logger.debug("Webhook notifications not configured, skipping")
            return
        
        logger.info(f"STUB: Would send webhook notification: {payload.title}")
        
        # TODO: Implement actual webhook sending
        # import requests
        #
        # response = requests.post(
        #     settings.WEBHOOK_URL,
        #     json=payload.to_dict(),
        #     timeout=10,
        # )
        # response.raise_for_status()
    
    def send_alert_notification(
        self, 
        alert_type: str, 
        review_data: Dict[str, Any]
    ):
        """
        Send notification for a review alert.
        
        Args:
            alert_type: Type of alert
            review_data: Review data to include
        """
        payload = NotificationPayload(
            title=f"Review Alert: {alert_type}",
            message=self._format_alert_message(alert_type, review_data),
            severity="high" if "negative" in alert_type.lower() else "medium",
            data=review_data,
        )
        
        self.notify(payload)
    
    def _format_alert_message(
        self, 
        alert_type: str, 
        review_data: Dict[str, Any]
    ) -> str:
        """Format an alert message from review data."""
        lines = [
            f"Alert Type: {alert_type}",
            f"Platform: {review_data.get('platform_name', 'Unknown')}",
            f"Rating: {review_data.get('rating', 'N/A')}/5",
            f"Reviewer: {review_data.get('reviewer_name', 'Anonymous')}",
            "",
            "Review:",
            review_data.get('review_text', 'No text')[:500],
        ]
        
        return "\n".join(lines)


class WeeklyDigestService:
    """
    Service for generating and sending weekly digest emails.
    
    STUB: To be fully implemented when email is configured.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.notification_service = NotificationService()
    
    def generate_digest(self) -> Dict[str, Any]:
        """
        Generate weekly digest data.
        
        Returns:
            Digest data including stats and notable reviews
        """
        from models import Review, Platform, ReviewSnapshot
        from datetime import timedelta
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Get reviews from the past week
        recent_reviews = self.db.query(Review).filter(
            Review.created_at >= week_ago
        ).all()
        
        # Compile statistics
        stats = {
            "period_start": week_ago.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "total_new_reviews": len(recent_reviews),
            "average_rating": None,
            "positive_reviews": 0,
            "negative_reviews": 0,
            "neutral_reviews": 0,
            "reviews_needing_response": 0,
            "platform_breakdown": {},
            "notable_reviews": [],
        }
        
        if recent_reviews:
            ratings = [r.rating for r in recent_reviews if r.rating]
            if ratings:
                stats["average_rating"] = sum(ratings) / len(ratings)
            
            for review in recent_reviews:
                if review.sentiment_label == "positive":
                    stats["positive_reviews"] += 1
                elif review.sentiment_label == "negative":
                    stats["negative_reviews"] += 1
                else:
                    stats["neutral_reviews"] += 1
                
                if review.needs_response and not review.response_text:
                    stats["reviews_needing_response"] += 1
                
                # Track by platform
                platform = review.platform
                if platform:
                    name = platform.name
                    if name not in stats["platform_breakdown"]:
                        stats["platform_breakdown"][name] = {"count": 0, "ratings": []}
                    stats["platform_breakdown"][name]["count"] += 1
                    if review.rating:
                        stats["platform_breakdown"][name]["ratings"].append(review.rating)
            
            # Find notable reviews (very positive or negative)
            notable = sorted(
                recent_reviews,
                key=lambda r: abs(r.sentiment_score or 0),
                reverse=True
            )[:5]
            
            stats["notable_reviews"] = [
                {
                    "id": r.id,
                    "platform": r.platform.name if r.platform else "Unknown",
                    "rating": r.rating,
                    "sentiment": r.sentiment_label,
                    "excerpt": (r.review_text or "")[:200],
                }
                for r in notable
            ]
        
        # Calculate platform averages
        for platform_name, data in stats["platform_breakdown"].items():
            if data["ratings"]:
                data["average_rating"] = sum(data["ratings"]) / len(data["ratings"])
            del data["ratings"]  # Don't include raw ratings in output
        
        return stats
    
    def send_digest(self):
        """
        Generate and send the weekly digest.
        
        STUB: Email sending to be implemented.
        """
        logger.info("Generating weekly digest...")
        
        digest = self.generate_digest()
        
        payload = NotificationPayload(
            title="Sage House Reviews - Weekly Digest",
            message=self._format_digest_email(digest),
            severity="info",
            data=digest,
        )
        
        # STUB: Would send via email
        logger.info(
            f"STUB: Would send weekly digest - "
            f"{digest['total_new_reviews']} reviews, "
            f"avg rating: {digest.get('average_rating', 'N/A')}"
        )
        
        return digest
    
    def _format_digest_email(self, digest: Dict[str, Any]) -> str:
        """Format digest data as email body."""
        lines = [
            "Weekly Review Summary",
            "=" * 40,
            "",
            f"Period: {digest['period_start'][:10]} to {digest['period_end'][:10]}",
            "",
            "Overall Statistics:",
            f"  - New Reviews: {digest['total_new_reviews']}",
            f"  - Average Rating: {digest.get('average_rating', 'N/A'):.1f}/5" if digest.get('average_rating') else "  - Average Rating: N/A",
            f"  - Positive: {digest['positive_reviews']}",
            f"  - Neutral: {digest['neutral_reviews']}",
            f"  - Negative: {digest['negative_reviews']}",
            f"  - Awaiting Response: {digest['reviews_needing_response']}",
            "",
        ]
        
        if digest["platform_breakdown"]:
            lines.append("By Platform:")
            for platform, data in digest["platform_breakdown"].items():
                avg = data.get('average_rating')
                avg_str = f"{avg:.1f}/5" if avg else "N/A"
                lines.append(f"  - {platform}: {data['count']} reviews (avg: {avg_str})")
        
        if digest["notable_reviews"]:
            lines.append("")
            lines.append("Notable Reviews:")
            for review in digest["notable_reviews"]:
                lines.append(f"  [{review['platform']}] {review['rating']}/5 - {review['excerpt'][:100]}...")
        
        return "\n".join(lines)

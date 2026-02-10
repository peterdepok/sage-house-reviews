"""
Synchronization service for fetching and storing reviews.
Handles deduplication, sentiment analysis, and alert generation.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models import Platform, Review, ReviewSnapshot, AlertType
from scrapers import get_scraper, BaseScraper, ReviewData
from services.sentiment import analyze_sentiment
from services.alerts import AlertService
from database import get_db_context


logger = logging.getLogger(__name__)


class SyncService:
    """
    Service for synchronizing reviews from all platforms.
    
    Responsibilities:
    - Fetch reviews from each platform using appropriate scraper
    - Deduplicate reviews (upsert logic)
    - Run sentiment analysis on new/updated reviews
    - Create snapshots for trend tracking
    - Generate alerts for notable reviews
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.alert_service = AlertService(db)
    
    def sync_all_platforms(self) -> Dict[str, Any]:
        """
        Synchronize reviews from all active platforms.
        
        Returns:
            Summary of sync results
        """
        platforms = self.db.query(Platform).filter(Platform.is_active == True).all()
        
        results = []
        total_new = 0
        total_updated = 0
        
        for platform in platforms:
            try:
                result = self.sync_platform(platform)
                results.append(result)
                total_new += result.get("new_reviews", 0)
                total_updated += result.get("updated_reviews", 0)
            except Exception as e:
                logger.exception(f"Failed to sync platform {platform.name}: {e}")
                results.append({
                    "platform_id": platform.id,
                    "platform_name": platform.name,
                    "success": False,
                    "error": str(e),
                })
        
        return {
            "synced_at": datetime.utcnow().isoformat(),
            "platforms_synced": len(platforms),
            "total_new_reviews": total_new,
            "total_updated_reviews": total_updated,
            "results": results,
        }
    
    def sync_platform(self, platform: Platform) -> Dict[str, Any]:
        """
        Synchronize reviews for a single platform.
        
        Args:
            platform: Platform to sync
            
        Returns:
            Sync result for this platform
        """
        logger.info(f"Starting sync for platform: {platform.name}")
        
        result = {
            "platform_id": platform.id,
            "platform_name": platform.name,
            "success": True,
            "new_reviews": 0,
            "updated_reviews": 0,
            "errors": [],
        }
        
        try:
            # Get the appropriate scraper
            scraper_class = get_scraper(platform.name)
            config = self._get_scraper_config(platform)
            scraper = scraper_class(config)
            
            # Fetch reviews
            scraper_result = scraper.run()
            
            if not scraper_result.success:
                result["success"] = False
                result["errors"] = scraper_result.errors
                return result
            
            # Process each review
            for review_data in scraper_result.reviews:
                try:
                    is_new = self._upsert_review(platform.id, review_data)
                    if is_new:
                        result["new_reviews"] += 1
                    else:
                        result["updated_reviews"] += 1
                except Exception as e:
                    logger.error(f"Failed to save review: {e}")
                    result["errors"].append(str(e))
            
            # Create snapshot
            self._create_snapshot(
                platform, 
                scraper_result.total_count, 
                scraper_result.average_rating,
                result["new_reviews"]
            )
            
            # Update platform last_sync
            platform.last_sync = datetime.utcnow()
            self.db.commit()
            
            logger.info(
                f"Completed sync for {platform.name}: "
                f"{result['new_reviews']} new, {result['updated_reviews']} updated"
            )
            
        except ValueError as e:
            # No scraper available for platform
            result["success"] = False
            result["errors"].append(str(e))
        except Exception as e:
            logger.exception(f"Sync failed for {platform.name}")
            result["success"] = False
            result["errors"].append(str(e))
        
        return result
    
    def sync_platforms_by_ids(self, platform_ids: List[int]) -> Dict[str, Any]:
        """
        Synchronize specific platforms by ID.
        
        Args:
            platform_ids: List of platform IDs to sync
            
        Returns:
            Summary of sync results
        """
        platforms = self.db.query(Platform).filter(
            Platform.id.in_(platform_ids),
            Platform.is_active == True
        ).all()
        
        results = []
        total_new = 0
        total_updated = 0
        
        for platform in platforms:
            result = self.sync_platform(platform)
            results.append(result)
            total_new += result.get("new_reviews", 0)
            total_updated += result.get("updated_reviews", 0)
        
        return {
            "synced_at": datetime.utcnow().isoformat(),
            "platforms_synced": len(platforms),
            "total_new_reviews": total_new,
            "total_updated_reviews": total_updated,
            "results": results,
        }
    
    def _get_scraper_config(self, platform: Platform) -> Dict[str, Any]:
        """Get scraper configuration for a platform."""
        config = platform.config_json or {}
        
        # Add any credentials reference
        if platform.credentials_ref:
            config["credentials_ref"] = platform.credentials_ref
        
        return config
    
    def _upsert_review(self, platform_id: int, review_data: ReviewData) -> bool:
        """
        Insert or update a review.
        
        Args:
            platform_id: ID of the platform
            review_data: Parsed review data
            
        Returns:
            True if new review was created, False if existing was updated
        """
        # Check for existing review
        existing = self.db.query(Review).filter(
            Review.platform_id == platform_id,
            Review.external_review_id == review_data.external_id
        ).first()
        
        # Analyze sentiment
        sentiment_result = analyze_sentiment(
            review_data.review_text or "", 
            review_data.rating
        )
        
        if existing:
            # Update existing review
            existing.reviewer_name = review_data.reviewer_name
            existing.reviewer_profile_url = review_data.reviewer_profile_url
            existing.rating = review_data.rating
            existing.review_text = review_data.review_text
            existing.review_date = review_data.review_date
            existing.sentiment_score = sentiment_result.score
            existing.sentiment_label = sentiment_result.label.value
            existing.raw_json = review_data.raw_json
            existing.updated_at = datetime.utcnow()
            
            self.db.commit()
            return False
        
        # Create new review
        review = Review(
            platform_id=platform_id,
            external_review_id=review_data.external_id,
            reviewer_name=review_data.reviewer_name,
            reviewer_profile_url=review_data.reviewer_profile_url,
            rating=review_data.rating,
            review_text=review_data.review_text,
            review_date=review_data.review_date,
            sentiment_score=sentiment_result.score,
            sentiment_label=sentiment_result.label.value,
            raw_json=review_data.raw_json,
            needs_response=self._needs_response(review_data.rating, sentiment_result.score),
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        # Check if alert should be created
        self._check_alerts(review)
        
        return True
    
    def _needs_response(self, rating: Optional[float], sentiment_score: float) -> bool:
        """Determine if a review needs a response."""
        # Flag negative reviews for response
        if rating is not None and rating <= 3:
            return True
        if sentiment_score < -0.3:
            return True
        return False
    
    def _check_alerts(self, review: Review):
        """Check if alerts should be created for this review."""
        # Alert for negative reviews
        if review.rating is not None and review.rating <= 2:
            self.alert_service.create_alert(
                review_id=review.id,
                alert_type=AlertType.NEGATIVE_REVIEW,
                title=f"Negative Review ({review.rating}/5)",
                message=f"New {review.rating}-star review received",
                severity="high" if review.rating == 1 else "medium",
            )
        
        # Alert for very negative sentiment
        if review.sentiment_score is not None and review.sentiment_score < -0.5:
            self.alert_service.create_alert(
                review_id=review.id,
                alert_type=AlertType.RESPONSE_NEEDED,
                title="Review Needs Attention",
                message="Review has very negative sentiment",
                severity="medium",
            )
    
    def _create_snapshot(
        self, 
        platform: Platform, 
        total_count: Optional[int],
        average_rating: Optional[float],
        new_reviews: int
    ):
        """Create a snapshot of platform metrics."""
        # Count reviews by sentiment
        reviews = self.db.query(Review).filter(Review.platform_id == platform.id).all()
        
        positive = sum(1 for r in reviews if r.sentiment_label == "positive")
        negative = sum(1 for r in reviews if r.sentiment_label == "negative")
        neutral = sum(1 for r in reviews if r.sentiment_label == "neutral")
        
        # Calculate response rate
        total_reviews = len(reviews)
        responded = sum(1 for r in reviews if r.response_text)
        response_rate = (responded / total_reviews * 100) if total_reviews > 0 else None
        
        snapshot = ReviewSnapshot(
            platform_id=platform.id,
            snapshot_date=datetime.utcnow(),
            total_reviews=total_count or total_reviews,
            average_rating=average_rating,
            new_reviews_count=new_reviews,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            response_rate=response_rate,
        )
        
        self.db.add(snapshot)
        self.db.commit()


def run_sync():
    """
    Run a full sync (called by scheduler).
    Uses its own database context.
    """
    logger.info("Starting scheduled sync")
    
    with get_db_context() as db:
        service = SyncService(db)
        result = service.sync_all_platforms()
        
    logger.info(
        f"Scheduled sync complete: "
        f"{result['total_new_reviews']} new, "
        f"{result['total_updated_reviews']} updated"
    )
    
    return result

"""
Facebook Graph API scraper for Facebook Page reviews/recommendations.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class FacebookScraper(BaseScraper):
    """
    Scraper for Facebook Page reviews using Graph API.
    
    Requires:
    - FACEBOOK_ACCESS_TOKEN: Page access token with pages_read_user_content permission
    - FACEBOOK_PAGE_ID: The Facebook Page ID
    
    Note: Facebook changed from star ratings to recommendations (recommend/don't recommend)
    in 2018. This scraper handles both legacy ratings and new recommendations.
    """
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.access_token = self.config.get("access_token") or settings.FACEBOOK_ACCESS_TOKEN
        self.page_id = self.config.get("page_id") or settings.FACEBOOK_PAGE_ID
        
        if not self.access_token:
            logger.warning("FACEBOOK_ACCESS_TOKEN not configured - Facebook scraper disabled")
    
    @property
    def platform_name(self) -> str:
        return "facebook"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews/recommendations from Facebook Graph API.
        """
        result = ScraperResult(success=True)
        
        if not self.access_token or not self.page_id:
            result.success = False
            result.add_error("Facebook API credentials not configured")
            return result
        
        # Get page info first
        page_info = self._get_page_info()
        if page_info:
            result.average_rating = page_info.get("overall_star_rating")
            result.total_count = page_info.get("rating_count")
            result.metadata["page_name"] = page_info.get("name")
        
        # Get reviews (ratings/recommendations)
        reviews_data = self._get_ratings()
        
        for review in reviews_data:
            try:
                review_data = self._parse_review(review)
                result.add_review(review_data)
            except Exception as e:
                result.add_error(f"Failed to parse review: {e}")
                continue
        
        self.logger.info(
            f"Fetched {len(result.reviews)} reviews from Facebook. "
            f"Total: {result.total_count}, Average: {result.average_rating}"
        )
        
        return result
    
    def _get_page_info(self) -> Optional[Dict[str, Any]]:
        """Get Facebook Page information."""
        url = f"{self.BASE_URL}/{self.page_id}"
        
        params = {
            "access_token": self.access_token,
            "fields": "name,overall_star_rating,rating_count,fan_count,link",
        }
        
        try:
            response = self._make_request(url, params=params)
            return response.json()
        except Exception as e:
            self.logger.exception(f"Failed to get page info: {e}")
            return None
    
    def _get_ratings(self) -> List[Dict[str, Any]]:
        """
        Get ratings/recommendations from Facebook.
        
        Note: Accessing ratings requires specific permissions and may be
        restricted based on your app's access level.
        """
        url = f"{self.BASE_URL}/{self.page_id}/ratings"
        
        all_reviews = []
        
        params = {
            "access_token": self.access_token,
            "fields": "reviewer,rating,recommendation_type,review_text,created_time,open_graph_story",
            "limit": 100,
        }
        
        try:
            while True:
                response = self._make_request(url, params=params)
                data = response.json()
                
                reviews = data.get("data", [])
                all_reviews.extend(reviews)
                
                # Handle pagination
                paging = data.get("paging", {})
                next_url = paging.get("next")
                
                if not next_url or len(all_reviews) >= 500:  # Safety limit
                    break
                    
                url = next_url
                params = {}  # Next URL includes all params
                
        except Exception as e:
            self.logger.exception(f"Failed to get ratings: {e}")
        
        return all_reviews
    
    def _parse_review(self, review: Dict[str, Any]) -> ReviewData:
        """Parse a Facebook review into standardized format."""
        reviewer = review.get("reviewer", {})
        
        # Handle both old star ratings and new recommendations
        rating = review.get("rating")
        if rating is None:
            # New recommendation system: recommend = 5, don't recommend = 1
            recommendation = review.get("recommendation_type")
            if recommendation == "positive":
                rating = 5.0
            elif recommendation == "negative":
                rating = 1.0
        
        # Parse date
        created_time = review.get("created_time", "")
        review_date = self._parse_date(created_time)
        
        return ReviewData(
            external_id=review.get("open_graph_story", {}).get("id", str(hash(str(review)))),
            reviewer_name=reviewer.get("name"),
            reviewer_profile_url=None,  # Facebook doesn't expose this easily
            rating=float(rating) if rating else None,
            review_text=review.get("review_text"),
            review_date=review_date,
            raw_json=review,
        )

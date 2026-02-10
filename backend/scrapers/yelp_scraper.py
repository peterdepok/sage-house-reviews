"""
Yelp Fusion API scraper for Yelp reviews.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class YelpScraper(BaseScraper):
    """
    Scraper for Yelp reviews using Yelp Fusion API.
    
    Requires:
    - YELP_API_KEY: Your Yelp Fusion API key
    - YELP_BUSINESS_ID: The Yelp business ID or alias
    
    Note: Yelp API only returns up to 3 reviews per request.
    For full review access, you would need to scrape the website
    (which may violate ToS) or use Yelp's official partnership programs.
    """
    
    BASE_URL = "https://api.yelp.com/v3"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key") or settings.YELP_API_KEY
        self.business_id = self.config.get("business_id") or settings.YELP_BUSINESS_ID
        
        if not self.api_key:
            logger.warning("YELP_API_KEY not configured - Yelp scraper disabled")
        
        # Set up authentication header
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    @property
    def platform_name(self) -> str:
        return "yelp"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews from Yelp Fusion API.
        
        Returns business info and up to 3 reviews.
        """
        result = ScraperResult(success=True)
        
        if not self.api_key or not self.business_id:
            result.success = False
            result.add_error("Yelp API credentials not configured")
            return result
        
        # Get business details first
        business_info = self._get_business_details()
        if business_info:
            result.average_rating = business_info.get("rating")
            result.total_count = business_info.get("review_count")
            result.metadata["business_name"] = business_info.get("name")
            result.metadata["url"] = business_info.get("url")
        
        # Get reviews
        reviews_data = self._get_reviews()
        
        for review in reviews_data:
            try:
                review_data = self._parse_review(review)
                result.add_review(review_data)
            except Exception as e:
                result.add_error(f"Failed to parse review: {e}")
                continue
        
        self.logger.info(
            f"Fetched {len(result.reviews)} reviews from Yelp. "
            f"Total reviews: {result.total_count}, Average: {result.average_rating}"
        )
        
        return result
    
    def _get_business_details(self) -> Optional[Dict[str, Any]]:
        """Get business details from Yelp."""
        url = f"{self.BASE_URL}/businesses/{self.business_id}"
        
        try:
            response = self._make_request(url)
            return response.json()
        except Exception as e:
            self.logger.exception(f"Failed to get business details: {e}")
            return None
    
    def _get_reviews(self) -> list:
        """Get reviews from Yelp API."""
        url = f"{self.BASE_URL}/businesses/{self.business_id}/reviews"
        
        params = {
            "limit": 50,  # Max per request
            "sort_by": "newest",
        }
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            return data.get("reviews", [])
        except Exception as e:
            self.logger.exception(f"Failed to get reviews: {e}")
            return []
    
    def _parse_review(self, review: Dict[str, Any]) -> ReviewData:
        """Parse a Yelp review into standardized format."""
        user = review.get("user", {})
        
        # Parse the review date
        review_date = self._parse_date(review.get("time_created", ""))
        
        return ReviewData(
            external_id=review.get("id", ""),
            reviewer_name=user.get("name"),
            reviewer_profile_url=user.get("profile_url"),
            rating=float(review.get("rating", 0)),
            review_text=review.get("text"),
            review_date=review_date,
            raw_json=review,
        )

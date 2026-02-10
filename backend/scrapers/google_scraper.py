"""
Google Places API scraper for Google Business Profile reviews.
This is the primary review source and should be fully functional.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class GoogleReviewsScraper(BaseScraper):
    """
    Scraper for Google Business Profile reviews using Places API.
    
    Requires:
    - GOOGLE_PLACES_API_KEY: Your Google Cloud API key
    - GOOGLE_PLACE_ID: The Place ID for Sage House
    
    Note: The Places API has limitations on reviews:
    - Only returns up to 5 most relevant reviews by default
    - Requires Places API (New) for more comprehensive access
    """
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key") or settings.GOOGLE_PLACES_API_KEY
        self.place_id = self.config.get("place_id") or settings.GOOGLE_PLACE_ID
        
        if not self.api_key:
            raise ValueError("GOOGLE_PLACES_API_KEY is required")
        if not self.place_id:
            raise ValueError("GOOGLE_PLACE_ID is required")
    
    @property
    def platform_name(self) -> str:
        return "google"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews from Google Places API.
        
        Uses the Place Details endpoint to get reviews.
        Note: This only returns the 5 most helpful reviews.
        For full review access, consider Google's Business Profile API
        (requires verification as the business owner).
        """
        result = ScraperResult(success=True)
        
        # First, get place details with reviews
        details = self._get_place_details()
        
        if not details:
            result.success = False
            result.add_error("Failed to fetch place details")
            return result
        
        # Extract overall rating and review count
        result.average_rating = details.get("rating")
        result.total_count = details.get("user_ratings_total")
        result.metadata["place_name"] = details.get("name")
        result.metadata["formatted_address"] = details.get("formatted_address")
        
        # Process reviews
        reviews_data = details.get("reviews", [])
        
        for review in reviews_data:
            try:
                review_data = self._parse_review(review)
                result.add_review(review_data)
            except Exception as e:
                result.add_error(f"Failed to parse review: {e}")
                continue
        
        self.logger.info(
            f"Fetched {len(result.reviews)} reviews from Google. "
            f"Total reviews: {result.total_count}, Average: {result.average_rating}"
        )
        
        return result
    
    def _get_place_details(self) -> Optional[Dict[str, Any]]:
        """
        Get place details including reviews from Google Places API.
        
        Returns:
            Place details dict or None on failure
        """
        url = f"{self.BASE_URL}/details/json"
        
        params = {
            "place_id": self.place_id,
            "key": self.api_key,
            "fields": "name,formatted_address,rating,user_ratings_total,reviews",
            "reviews_sort": "newest",  # Get newest reviews
        }
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            
            if data.get("status") != "OK":
                error_msg = data.get("error_message", data.get("status"))
                self.logger.error(f"Google API error: {error_msg}")
                return None
            
            return data.get("result")
            
        except Exception as e:
            self.logger.exception(f"Failed to get place details: {e}")
            return None
    
    def _parse_review(self, review: Dict[str, Any]) -> ReviewData:
        """
        Parse a Google review into standardized format.
        
        Args:
            review: Raw review data from Google API
            
        Returns:
            Standardized ReviewData
        """
        # Google uses Unix timestamp for review time
        review_time = review.get("time")
        review_date = None
        if review_time:
            review_date = datetime.fromtimestamp(review_time)
        
        return ReviewData(
            external_id=f"google_{review.get('time')}_{hash(review.get('author_name', ''))}",
            reviewer_name=review.get("author_name"),
            reviewer_profile_url=review.get("author_url"),
            rating=float(review.get("rating", 0)),
            review_text=review.get("text"),
            review_date=review_date,
            raw_json=review,
        )
    
    def get_place_info(self) -> Optional[Dict[str, Any]]:
        """
        Get basic place information without reviews.
        Useful for validation and displaying business info.
        
        Returns:
            Place information dict or None
        """
        url = f"{self.BASE_URL}/details/json"
        
        params = {
            "place_id": self.place_id,
            "key": self.api_key,
            "fields": "name,formatted_address,formatted_phone_number,website,url,rating,user_ratings_total,opening_hours,photos",
        }
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            
            if data.get("status") == "OK":
                return data.get("result")
            return None
            
        except Exception as e:
            self.logger.exception(f"Failed to get place info: {e}")
            return None


class GooglePlacesNewScraper(BaseScraper):
    """
    Alternative scraper using the newer Places API (New).
    This API provides more comprehensive review access but requires
    different authentication and has different pricing.
    
    Note: This is a stub for future implementation.
    The new API requires OAuth2 and has a different structure.
    """
    
    BASE_URL = "https://places.googleapis.com/v1/places"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key") or settings.GOOGLE_PLACES_API_KEY
        self.place_id = self.config.get("place_id") or settings.GOOGLE_PLACE_ID
        
        # The new API requires additional headers
        self.session.headers.update({
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "reviews,rating,userRatingCount",
        })
    
    @property
    def platform_name(self) -> str:
        return "google_new"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews using the new Places API.
        
        Note: This is a stub implementation.
        The actual implementation would require:
        1. OAuth2 authentication flow
        2. Different request structure
        3. Pagination handling
        """
        result = ScraperResult(success=False)
        result.add_error("Google Places (New) API scraper not yet implemented")
        return result

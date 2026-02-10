"""
Medicare.gov Care Compare data fetcher.
Pulls quality ratings and inspection data for healthcare facilities.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class MedicareScraper(BaseScraper):
    """
    Data fetcher for Medicare.gov Care Compare quality ratings.
    
    Note: Medicare Care Compare provides quality ratings for nursing homes,
    not assisted living facilities. This scraper may have limited applicability
    depending on Sage House's Medicare certification status.
    
    Requires:
    - MEDICARE_PROVIDER_ID: The CMS Certification Number (CCN) or Provider ID
    
    Data available:
    - Overall quality star rating (1-5)
    - Health inspection ratings
    - Staffing ratings
    - Quality measure ratings
    
    The Care Compare API is publicly available but may require registration.
    """
    
    # Medicare Care Compare API (public dataset)
    BASE_URL = "https://data.cms.gov/provider-data/api/1/datastore/query"
    
    # Dataset identifiers for different data types
    DATASETS = {
        "provider_info": "4pq5-n9py",  # Provider Information
        "quality_measures": "djen-97ju",  # Quality Measures
        "health_inspections": "ft4h-xyiu",  # Health Deficiencies
        "staffing": "bny9-9c6u",  # Staffing
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.provider_id = self.config.get("provider_id") or settings.MEDICARE_PROVIDER_ID
        
        if not self.provider_id:
            logger.warning("MEDICARE_PROVIDER_ID not configured - Medicare scraper disabled")
    
    @property
    def platform_name(self) -> str:
        return "medicare"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch quality ratings from Medicare Care Compare.
        
        Note: Medicare doesn't have "reviews" per se, but provides
        quality ratings which we treat as a special type of review.
        """
        result = ScraperResult(success=True)
        
        if not self.provider_id:
            result.success = False
            result.add_error("Medicare Provider ID not configured")
            return result
        
        try:
            # Fetch provider info and ratings
            provider_info = self._fetch_provider_info()
            
            if provider_info:
                # Create a synthetic "review" from the quality rating
                review = self._create_rating_review(provider_info)
                if review:
                    result.add_review(review)
                
                # Store metrics
                result.average_rating = provider_info.get("overall_rating")
                result.total_count = 1  # Medicare only gives aggregate ratings
                result.metadata = provider_info
            else:
                result.add_error("Provider not found in Medicare database")
            
            self.logger.info(
                f"Fetched Medicare quality rating: {result.average_rating}"
            )
            
        except Exception as e:
            result.success = False
            result.add_error(f"Failed to fetch Medicare data: {e}")
        
        return result
    
    def _fetch_provider_info(self) -> Optional[Dict[str, Any]]:
        """
        Fetch provider information and quality ratings.
        
        Returns:
            Provider data dict or None if not found
        """
        # Use the CMS Provider Data API
        url = f"{self.BASE_URL}/{self.DATASETS['provider_info']}"
        
        params = {
            "conditions[0][property]": "federal_provider_number",
            "conditions[0][value]": self.provider_id,
            "conditions[0][operator]": "=",
        }
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            
            results = data.get("results", [])
            if results:
                provider = results[0]
                return self._parse_provider_data(provider)
            
            return None
            
        except Exception as e:
            self.logger.exception(f"Failed to fetch provider info: {e}")
            return None
    
    def _parse_provider_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw provider data into a clean format."""
        return {
            "provider_id": data.get("federal_provider_number"),
            "provider_name": data.get("provider_name"),
            "address": data.get("provider_address"),
            "city": data.get("provider_city"),
            "state": data.get("provider_state"),
            "zip": data.get("provider_zip_code"),
            "phone": data.get("provider_phone_number"),
            "ownership_type": data.get("ownership_type"),
            "number_of_beds": data.get("number_of_certified_beds"),
            "number_of_residents": data.get("average_number_of_residents_per_day"),
            # Star ratings
            "overall_rating": self._parse_star_rating(data.get("overall_rating")),
            "health_inspection_rating": self._parse_star_rating(data.get("health_inspection_rating")),
            "staffing_rating": self._parse_star_rating(data.get("staffing_rating")),
            "quality_measure_rating": self._parse_star_rating(data.get("qm_rating")),
            # Dates
            "last_standard_survey_date": data.get("date_of_last_standard_health_inspection"),
            "data_date": data.get("processing_date"),
        }
    
    def _parse_star_rating(self, rating: Any) -> Optional[float]:
        """Parse a star rating value to float."""
        if rating is None:
            return None
        try:
            return float(rating)
        except (ValueError, TypeError):
            return None
    
    def _create_rating_review(self, provider_info: Dict[str, Any]) -> Optional[ReviewData]:
        """
        Create a synthetic review from Medicare quality ratings.
        
        This allows Medicare ratings to be displayed alongside actual reviews.
        """
        overall_rating = provider_info.get("overall_rating")
        if overall_rating is None:
            return None
        
        # Build a summary text of all ratings
        review_text = self._build_rating_summary(provider_info)
        
        return ReviewData(
            external_id=f"medicare_{self.provider_id}_{datetime.now().strftime('%Y%m')}",
            reviewer_name="Medicare Care Compare",
            rating=overall_rating,
            review_text=review_text,
            review_date=datetime.now(),
            raw_json=provider_info,
        )
    
    def _build_rating_summary(self, info: Dict[str, Any]) -> str:
        """Build a summary text from Medicare ratings."""
        lines = [
            f"Medicare Care Compare Quality Rating Summary",
            f"",
            f"Overall Rating: {info.get('overall_rating', 'N/A')} / 5 stars",
            f"Health Inspection: {info.get('health_inspection_rating', 'N/A')} / 5 stars",
            f"Staffing: {info.get('staffing_rating', 'N/A')} / 5 stars",
            f"Quality Measures: {info.get('quality_measure_rating', 'N/A')} / 5 stars",
        ]
        
        if info.get("last_standard_survey_date"):
            lines.append(f"")
            lines.append(f"Last Inspection: {info.get('last_standard_survey_date')}")
        
        return "\n".join(lines)
    
    def fetch_health_deficiencies(self) -> List[Dict[str, Any]]:
        """
        Fetch detailed health inspection deficiencies.
        
        Returns:
            List of deficiency records
        """
        url = f"{self.BASE_URL}/{self.DATASETS['health_inspections']}"
        
        params = {
            "conditions[0][property]": "federal_provider_number",
            "conditions[0][value]": self.provider_id,
            "conditions[0][operator]": "=",
            "limit": 100,
            "sort[0][property]": "survey_date",
            "sort[0][order]": "desc",
        }
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            self.logger.exception(f"Failed to fetch deficiencies: {e}")
            return []

"""
Web scraper for SeniorAdvisor.com reviews.
"""
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class SeniorAdvisorScraper(BaseScraper):
    """
    Web scraper for SeniorAdvisor.com facility reviews.
    
    Requires:
    - SENIOR_ADVISOR_URL: Full URL to the facility's page on senioradvisor.com
    
    Example URL: https://www.senioradvisor.com/local/sage-house-city-state
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.facility_url = self.config.get("url") or settings.SENIOR_ADVISOR_URL
        
        if not self.facility_url:
            logger.warning("SENIOR_ADVISOR_URL not configured - SeniorAdvisor scraper disabled")
    
    @property
    def platform_name(self) -> str:
        return "senioradvisor"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews from SeniorAdvisor.com by scraping the review page.
        """
        result = ScraperResult(success=True)
        
        if not self.facility_url:
            result.success = False
            result.add_error("SeniorAdvisor URL not configured")
            return result
        
        try:
            response = self._make_request(self.facility_url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract overall rating info
            rating_info = self._extract_rating_info(soup)
            result.average_rating = rating_info.get("average_rating")
            result.total_count = rating_info.get("total_count")
            result.metadata["facility_name"] = rating_info.get("facility_name")
            
            # Extract individual reviews
            reviews = self._extract_reviews(soup)
            
            for review in reviews:
                result.add_review(review)
            
            self.logger.info(
                f"Fetched {len(result.reviews)} reviews from SeniorAdvisor. "
                f"Total: {result.total_count}, Average: {result.average_rating}"
            )
            
        except Exception as e:
            result.success = False
            result.add_error(f"Failed to scrape SeniorAdvisor: {e}")
        
        return result
    
    def _extract_rating_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract overall rating information from the page."""
        info = {}
        
        try:
            # Look for structured data
            script_tags = soup.find_all("script", type="application/ld+json")
            for script in script_tags:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict) and "aggregateRating" in data:
                        agg = data["aggregateRating"]
                        info["average_rating"] = float(agg.get("ratingValue", 0))
                        info["total_count"] = int(agg.get("reviewCount", 0))
                        info["facility_name"] = data.get("name")
                        break
                except:
                    continue
            
            # Fallback to HTML
            if "average_rating" not in info:
                rating_elem = soup.find(class_=re.compile(r"overall-rating|star-rating", re.I))
                if rating_elem:
                    match = re.search(r"(\d+\.?\d*)", rating_elem.get_text())
                    if match:
                        info["average_rating"] = float(match.group(1))
            
            if "total_count" not in info:
                count_elem = soup.find(text=re.compile(r"(\d+)\s*reviews?", re.I))
                if count_elem:
                    match = re.search(r"(\d+)", str(count_elem))
                    if match:
                        info["total_count"] = int(match.group(1))
            
            if "facility_name" not in info:
                name_elem = soup.find("h1")
                if name_elem:
                    info["facility_name"] = name_elem.get_text(strip=True)
            
        except Exception as e:
            self.logger.warning(f"Error extracting rating info: {e}")
        
        return info
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[ReviewData]:
        """Extract individual reviews from the page."""
        reviews = []
        
        # Find review containers
        review_containers = soup.find_all(class_=re.compile(r"review-item|review-card|testimonial", re.I))
        
        for idx, container in enumerate(review_containers):
            try:
                review = self._parse_review_container(container, idx)
                if review:
                    reviews.append(review)
            except Exception as e:
                self.logger.warning(f"Failed to parse review container: {e}")
                continue
        
        return reviews
    
    def _parse_review_container(
        self, 
        container: BeautifulSoup, 
        idx: int
    ) -> Optional[ReviewData]:
        """Parse a single review container into ReviewData."""
        
        # Extract reviewer info
        reviewer_name = None
        name_elem = container.find(class_=re.compile(r"author|reviewer|name", re.I))
        if name_elem:
            reviewer_name = name_elem.get_text(strip=True)
        
        # Extract rating (SeniorAdvisor uses 5-star system)
        rating = None
        rating_elem = container.find(class_=re.compile(r"star|rating", re.I))
        if rating_elem:
            # Count filled stars or get from data attribute
            stars = rating_elem.get("data-rating") or rating_elem.get("aria-label")
            if stars:
                match = re.search(r"(\d+\.?\d*)", str(stars))
                if match:
                    rating = float(match.group(1))
            else:
                # Count star elements
                filled_stars = rating_elem.find_all(class_=re.compile(r"filled|active", re.I))
                if filled_stars:
                    rating = float(len(filled_stars))
        
        # Extract review text
        review_text = None
        text_elem = container.find(class_=re.compile(r"review-text|content|body|description", re.I))
        if text_elem:
            review_text = text_elem.get_text(strip=True)
        
        # Extract date
        review_date = None
        date_elem = container.find(class_=re.compile(r"date|time|posted", re.I))
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            review_date = self._parse_date(date_text)
        
        if not review_text and not rating:
            return None
        
        external_id = f"senioradvisor_{idx}_{hash((reviewer_name or '', review_text or ''))}"
        
        return ReviewData(
            external_id=external_id,
            reviewer_name=reviewer_name,
            rating=rating,
            review_text=review_text,
            review_date=review_date,
            raw_json={
                "source_url": self.facility_url,
            },
        )

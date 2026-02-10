"""
Web scraper for Caring.com reviews.
"""
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class CaringComScraper(BaseScraper):
    """
    Web scraper for Caring.com senior care facility reviews.
    
    Requires:
    - CARING_COM_URL: Full URL to the facility's review page on Caring.com
    
    Example URL: https://www.caring.com/senior-living/assisted-living/california/your-city/sage-house
    
    Note: Web scraping may be against Caring.com's ToS. This scraper
    implements polite scraping practices (rate limiting, user agent).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.facility_url = self.config.get("url") or settings.CARING_COM_URL
        
        if not self.facility_url:
            logger.warning("CARING_COM_URL not configured - Caring.com scraper disabled")
    
    @property
    def platform_name(self) -> str:
        return "caring"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews from Caring.com by scraping the review page.
        """
        result = ScraperResult(success=True)
        
        if not self.facility_url:
            result.success = False
            result.add_error("Caring.com URL not configured")
            return result
        
        try:
            # Fetch the main page
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
                f"Fetched {len(result.reviews)} reviews from Caring.com. "
                f"Total: {result.total_count}, Average: {result.average_rating}"
            )
            
        except Exception as e:
            result.success = False
            result.add_error(f"Failed to scrape Caring.com: {e}")
        
        return result
    
    def _extract_rating_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract overall rating information from the page."""
        info = {}
        
        try:
            # Try to find the facility name
            name_elem = soup.find("h1", class_=re.compile(r"facility|title|name", re.I))
            if name_elem:
                info["facility_name"] = name_elem.get_text(strip=True)
            
            # Try to find overall rating
            rating_elem = soup.find(class_=re.compile(r"rating|score|stars", re.I))
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Extract numeric rating
                match = re.search(r"(\d+\.?\d*)", rating_text)
                if match:
                    info["average_rating"] = float(match.group(1))
            
            # Try to find review count
            count_elem = soup.find(text=re.compile(r"\d+\s*reviews?", re.I))
            if count_elem:
                match = re.search(r"(\d+)", str(count_elem))
                if match:
                    info["total_count"] = int(match.group(1))
            
        except Exception as e:
            self.logger.warning(f"Error extracting rating info: {e}")
        
        return info
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[ReviewData]:
        """Extract individual reviews from the page."""
        reviews = []
        
        # Find review containers - the actual selectors will depend on Caring.com's HTML structure
        review_containers = soup.find_all(class_=re.compile(r"review|testimonial", re.I))
        
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
        
        # Extract reviewer name
        reviewer_name = None
        name_elem = container.find(class_=re.compile(r"author|reviewer|name", re.I))
        if name_elem:
            reviewer_name = name_elem.get_text(strip=True)
        
        # Extract rating
        rating = None
        rating_elem = container.find(class_=re.compile(r"rating|stars|score", re.I))
        if rating_elem:
            # Try to get rating from aria-label or text
            aria_label = rating_elem.get("aria-label", "")
            rating_match = re.search(r"(\d+\.?\d*)", aria_label or rating_elem.get_text())
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Extract review text
        review_text = None
        text_elem = container.find(class_=re.compile(r"text|content|body|comment", re.I))
        if text_elem:
            review_text = text_elem.get_text(strip=True)
        
        # Extract date
        review_date = None
        date_elem = container.find(class_=re.compile(r"date|time", re.I))
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            review_date = self._parse_date(date_text)
        
        # Skip if no meaningful content
        if not review_text and not rating:
            return None
        
        # Generate a unique ID
        external_id = f"caring_{idx}_{hash((reviewer_name or '', review_text or ''))}"
        
        return ReviewData(
            external_id=external_id,
            reviewer_name=reviewer_name,
            rating=rating,
            review_text=review_text,
            review_date=review_date,
            raw_json={
                "html": str(container)[:1000],  # Store truncated HTML for debugging
                "source_url": self.facility_url,
            },
        )

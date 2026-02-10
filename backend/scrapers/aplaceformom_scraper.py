"""
Web scraper for A Place for Mom reviews.
"""
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, ScraperResult, ReviewData
from config import settings


logger = logging.getLogger(__name__)


class APlaceForMomScraper(BaseScraper):
    """
    Web scraper for A Place for Mom (APFM) senior care facility reviews.
    
    Requires:
    - A_PLACE_FOR_MOM_URL: Full URL to the facility's page on aplaceformom.com
    
    Example URL: https://www.aplaceformom.com/community/sage-house-12345
    
    Note: Web scraping may be against APFM's ToS. This scraper
    implements polite scraping practices.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.facility_url = self.config.get("url") or settings.A_PLACE_FOR_MOM_URL
        
        if not self.facility_url:
            logger.warning("A_PLACE_FOR_MOM_URL not configured - APFM scraper disabled")
    
    @property
    def platform_name(self) -> str:
        return "aplaceformom"
    
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews from A Place for Mom by scraping the review page.
        """
        result = ScraperResult(success=True)
        
        if not self.facility_url:
            result.success = False
            result.add_error("A Place for Mom URL not configured")
            return result
        
        try:
            # Construct reviews URL (usually /reviews suffix)
            reviews_url = self._get_reviews_url()
            
            response = self._make_request(reviews_url)
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
                f"Fetched {len(result.reviews)} reviews from A Place for Mom. "
                f"Total: {result.total_count}, Average: {result.average_rating}"
            )
            
        except Exception as e:
            result.success = False
            result.add_error(f"Failed to scrape A Place for Mom: {e}")
        
        return result
    
    def _get_reviews_url(self) -> str:
        """Construct the reviews page URL."""
        # Remove trailing slash if present
        base_url = self.facility_url.rstrip("/")
        
        # Check if already pointing to reviews page
        if "/reviews" in base_url:
            return base_url
        
        return f"{base_url}/reviews"
    
    def _extract_rating_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract overall rating information from the page."""
        info = {}
        
        try:
            # APFM typically has structured rating display
            # Look for JSON-LD structured data first
            script_tags = soup.find_all("script", type="application/ld+json")
            for script in script_tags:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if "aggregateRating" in data:
                            agg = data["aggregateRating"]
                            info["average_rating"] = float(agg.get("ratingValue", 0))
                            info["total_count"] = int(agg.get("reviewCount", 0))
                        if "name" in data:
                            info["facility_name"] = data["name"]
                except:
                    continue
            
            # Fallback to HTML parsing
            if "average_rating" not in info:
                rating_elem = soup.find(attrs={"itemprop": "ratingValue"})
                if rating_elem:
                    rating_text = rating_elem.get("content") or rating_elem.get_text(strip=True)
                    match = re.search(r"(\d+\.?\d*)", rating_text)
                    if match:
                        info["average_rating"] = float(match.group(1))
            
            if "total_count" not in info:
                count_elem = soup.find(attrs={"itemprop": "reviewCount"})
                if count_elem:
                    count_text = count_elem.get("content") or count_elem.get_text(strip=True)
                    match = re.search(r"(\d+)", count_text)
                    if match:
                        info["total_count"] = int(match.group(1))
            
        except Exception as e:
            self.logger.warning(f"Error extracting rating info: {e}")
        
        return info
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[ReviewData]:
        """Extract individual reviews from the page."""
        reviews = []
        
        # Look for review containers with schema.org markup
        review_containers = soup.find_all(attrs={"itemprop": "review"})
        
        if not review_containers:
            # Fallback to class-based search
            review_containers = soup.find_all(class_=re.compile(r"review-item|review-card", re.I))
        
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
        name_elem = container.find(attrs={"itemprop": "author"})
        if not name_elem:
            name_elem = container.find(class_=re.compile(r"author|reviewer|name", re.I))
        if name_elem:
            reviewer_name = name_elem.get_text(strip=True)
        
        # Extract rating
        rating = None
        rating_elem = container.find(attrs={"itemprop": "ratingValue"})
        if rating_elem:
            rating_text = rating_elem.get("content") or rating_elem.get_text(strip=True)
            match = re.search(r"(\d+\.?\d*)", rating_text)
            if match:
                rating = float(match.group(1))
        
        # Extract review text
        review_text = None
        text_elem = container.find(attrs={"itemprop": "reviewBody"})
        if not text_elem:
            text_elem = container.find(class_=re.compile(r"review-text|review-body|content", re.I))
        if text_elem:
            review_text = text_elem.get_text(strip=True)
        
        # Extract date
        review_date = None
        date_elem = container.find(attrs={"itemprop": "datePublished"})
        if date_elem:
            date_text = date_elem.get("content") or date_elem.get_text(strip=True)
            review_date = self._parse_date(date_text)
        
        # Skip if no meaningful content
        if not review_text and not rating:
            return None
        
        # Generate a unique ID
        external_id = f"apfm_{idx}_{hash((reviewer_name or '', review_text or ''))}"
        
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

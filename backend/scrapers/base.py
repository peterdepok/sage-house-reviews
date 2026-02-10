"""
Base scraper interface and common utilities.
All platform scrapers must inherit from BaseScraper.
"""
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type
)
import requests
from requests.exceptions import RequestException

from config import settings


logger = logging.getLogger(__name__)


@dataclass
class ReviewData:
    """
    Standardized review data structure.
    All scrapers should return reviews in this format.
    """
    external_id: str
    reviewer_name: Optional[str] = None
    reviewer_profile_url: Optional[str] = None
    rating: Optional[float] = None  # Normalized to 5-point scale
    review_text: Optional[str] = None
    review_date: Optional[datetime] = None
    raw_json: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "external_review_id": self.external_id,
            "reviewer_name": self.reviewer_name,
            "reviewer_profile_url": self.reviewer_profile_url,
            "rating": self.rating,
            "review_text": self.review_text,
            "review_date": self.review_date,
            "raw_json": self.raw_json,
        }


@dataclass
class ScraperResult:
    """
    Result of a scraper run.
    Contains reviews and metadata about the scrape.
    """
    success: bool
    reviews: List[ReviewData] = field(default_factory=list)
    total_count: Optional[int] = None
    average_rating: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str):
        """Add an error message to the result."""
        self.errors.append(error)
        logger.error(f"Scraper error: {error}")
    
    def add_review(self, review: ReviewData):
        """Add a review to the result."""
        self.reviews.append(review)


class RateLimiter:
    """
    Simple rate limiter to prevent API abuse.
    Uses token bucket algorithm.
    """
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class BaseScraper(ABC):
    """
    Abstract base class for all platform scrapers.
    
    Provides common functionality:
    - HTTP session management with retry logic
    - Rate limiting
    - Error handling
    - Logging
    
    Subclasses must implement:
    - fetch_reviews(): The main method to fetch reviews
    - platform_name: Property returning the platform name
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the scraper.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.session = self._create_session()
        self.rate_limiter = RateLimiter(settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
        self.logger = logging.getLogger(f"scraper.{self.platform_name}")
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with default headers."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return session
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name for this scraper."""
        pass
    
    @abstractmethod
    def fetch_reviews(self) -> ScraperResult:
        """
        Fetch reviews from the platform.
        
        Returns:
            ScraperResult containing reviews and metadata
        """
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(RequestException),
        before_sleep=lambda retry_state: logger.warning(
            f"Request failed, retrying in {retry_state.next_action.sleep}s..."
        )
    )
    def _make_request(
        self, 
        url: str, 
        method: str = "GET",
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with retry logic and rate limiting.
        
        Args:
            url: The URL to request
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            RequestException: If all retries fail
        """
        self.rate_limiter.wait()
        
        self.logger.debug(f"{method} {url}")
        
        response = self.session.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        
        return response
    
    def _normalize_rating(
        self, 
        rating: float, 
        max_rating: float = 5.0
    ) -> float:
        """
        Normalize a rating to a 5-point scale.
        
        Args:
            rating: The original rating
            max_rating: The maximum rating on the source scale
            
        Returns:
            Rating normalized to 5-point scale
        """
        if max_rating == 5.0:
            return rating
        return (rating / max_rating) * 5.0
    
    def _parse_date(self, date_str: str, formats: List[str] = None) -> Optional[datetime]:
        """
        Parse a date string trying multiple formats.
        
        Args:
            date_str: Date string to parse
            formats: List of date formats to try
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        if not date_str:
            return None
            
        default_formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%m/%d/%Y",
        ]
        
        formats = formats or default_formats
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def run(self) -> ScraperResult:
        """
        Execute the scraper with error handling.
        
        Returns:
            ScraperResult with reviews or errors
        """
        self.logger.info(f"Starting {self.platform_name} scraper")
        
        try:
            result = self.fetch_reviews()
            self.logger.info(
                f"Completed {self.platform_name} scraper: "
                f"{len(result.reviews)} reviews fetched"
            )
            return result
            
        except Exception as e:
            self.logger.exception(f"Scraper failed: {e}")
            result = ScraperResult(success=False)
            result.add_error(str(e))
            return result
        
        finally:
            self.session.close()

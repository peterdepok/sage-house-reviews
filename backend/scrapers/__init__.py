"""
Scrapers module for fetching reviews from various platforms.
Each scraper implements the BaseScraper interface for consistency.
"""
from scrapers.base import BaseScraper, ScraperResult, ReviewData
from scrapers.google_scraper import GoogleReviewsScraper
from scrapers.yelp_scraper import YelpScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.caring_scraper import CaringComScraper
from scrapers.aplaceformom_scraper import APlaceForMomScraper
from scrapers.senioradvisor_scraper import SeniorAdvisorScraper
from scrapers.medicare_scraper import MedicareScraper

# Registry of available scrapers mapped by platform name
SCRAPER_REGISTRY = {
    "google": GoogleReviewsScraper,
    "yelp": YelpScraper,
    "facebook": FacebookScraper,
    "caring": CaringComScraper,
    "aplaceformom": APlaceForMomScraper,
    "senioradvisor": SeniorAdvisorScraper,
    "medicare": MedicareScraper,
}


def get_scraper(platform_name: str) -> type[BaseScraper]:
    """
    Get the scraper class for a given platform.
    
    Args:
        platform_name: Name of the platform (lowercase)
        
    Returns:
        Scraper class for the platform
        
    Raises:
        ValueError: If no scraper exists for the platform
    """
    scraper_class = SCRAPER_REGISTRY.get(platform_name.lower())
    if not scraper_class:
        raise ValueError(f"No scraper available for platform: {platform_name}")
    return scraper_class


__all__ = [
    "BaseScraper",
    "ScraperResult", 
    "ReviewData",
    "GoogleReviewsScraper",
    "YelpScraper",
    "FacebookScraper",
    "CaringComScraper",
    "APlaceForMomScraper",
    "SeniorAdvisorScraper",
    "MedicareScraper",
    "SCRAPER_REGISTRY",
    "get_scraper",
]

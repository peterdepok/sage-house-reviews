"""
Configuration management for the Sage House Review Dashboard.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Sage House Review Dashboard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sage_house_reviews.db"
    
    # API Keys - Platform Integrations
    GOOGLE_PLACES_API_KEY: Optional[str] = None
    GOOGLE_PLACE_ID: Optional[str] = None
    
    YELP_API_KEY: Optional[str] = None
    YELP_BUSINESS_ID: Optional[str] = None
    
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None
    
    # Scraper URLs (for platforms without APIs)
    CARING_COM_URL: Optional[str] = None
    A_PLACE_FOR_MOM_URL: Optional[str] = None
    SENIOR_ADVISOR_URL: Optional[str] = None
    MEDICARE_PROVIDER_ID: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    SCRAPER_DELAY_SECONDS: float = 2.0
    
    # Scheduler
    SYNC_INTERVAL_HOURS: int = 6
    ENABLE_SCHEDULER: bool = True
    
    # Notifications (stubs)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAIL: Optional[str] = None
    
    WEBHOOK_URL: Optional[str] = None
    
    # Sentiment Analysis
    SENTIMENT_ANALYZER: str = "vader"  # Options: vader, textblob
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()

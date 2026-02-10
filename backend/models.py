"""
SQLAlchemy models for the Sage House Review Dashboard.
Designed for easy migration from SQLite to PostgreSQL.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, 
    ForeignKey, Enum, JSON, Boolean, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base


class ApiType(str, PyEnum):
    """Type of data source - API or web scraping."""
    API = "api"
    SCRAPE = "scrape"


class AlertType(str, PyEnum):
    """Types of alerts that can be triggered."""
    NEGATIVE_REVIEW = "negative_review"
    LOW_RATING = "low_rating"
    RESPONSE_NEEDED = "response_needed"
    RATING_DROP = "rating_drop"
    NEW_REVIEW = "new_review"


class AlertStatus(str, PyEnum):
    """Status of an alert."""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Platform(Base):
    """
    Represents a review platform (Google, Yelp, etc.).
    Stores configuration for how to access each platform.
    """
    __tablename__ = "platforms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(500))
    api_type: Mapped[ApiType] = mapped_column(Enum(ApiType), default=ApiType.API)
    credentials_ref: Mapped[Optional[str]] = mapped_column(String(100))  # Reference to env var
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON)  # Platform-specific config
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="platform", cascade="all, delete-orphan")
    snapshots: Mapped[List["ReviewSnapshot"]] = relationship("ReviewSnapshot", back_populates="platform", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Platform(id={self.id}, name='{self.name}', api_type={self.api_type})>"


class Review(Base):
    """
    Individual review from any platform.
    Stores both parsed data and raw JSON for reference.
    """
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint('platform_id', 'external_review_id', name='uq_platform_review'),
        Index('ix_reviews_date', 'review_date'),
        Index('ix_reviews_rating', 'rating'),
        Index('ix_reviews_sentiment', 'sentiment_score'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), nullable=False)
    external_review_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Review content
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(255))
    reviewer_profile_url: Mapped[Optional[str]] = mapped_column(String(500))
    rating: Mapped[Optional[float]] = mapped_column(Float)  # Normalized to 5-point scale
    review_text: Mapped[Optional[str]] = mapped_column(Text)
    review_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Sentiment analysis
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20))  # positive, negative, neutral
    
    # Response tracking
    response_text: Mapped[Optional[str]] = mapped_column(Text)
    response_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    needs_response: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Raw data preservation
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    platform: Mapped["Platform"] = relationship("Platform", back_populates="reviews")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="review", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Review(id={self.id}, platform_id={self.platform_id}, rating={self.rating})>"


class ReviewSnapshot(Base):
    """
    Point-in-time snapshot of platform metrics.
    Used for tracking trends over time.
    """
    __tablename__ = "review_snapshots"
    __table_args__ = (
        Index('ix_snapshots_date', 'snapshot_date'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Metrics
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[Optional[float]] = mapped_column(Float)
    new_reviews_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Additional metrics
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    response_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    platform: Mapped["Platform"] = relationship("Platform", back_populates="snapshots")
    
    def __repr__(self):
        return f"<ReviewSnapshot(id={self.id}, platform_id={self.platform_id}, date={self.snapshot_date})>"


class Alert(Base):
    """
    Alerts triggered by review events (negative reviews, etc.).
    """
    __tablename__ = "alerts"
    __table_args__ = (
        Index('ix_alerts_status', 'status'),
        Index('ix_alerts_type', 'alert_type'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    review_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("reviews.id"))
    
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.PENDING)
    
    # Alert details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    review: Mapped[Optional["Review"]] = relationship("Review", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, status={self.status})>"


class ResponseTemplate(Base):
    """
    Templates for responding to reviews.
    """
    __tablename__ = "response_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50))  # positive, negative, general
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Optional[dict]] = mapped_column(JSON)  # Available template variables
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ResponseTemplate(id={self.id}, name='{self.name}')>"


# ============================================================================
# PHASE 2 STUB: Placements Table
# ============================================================================

class Placement(Base):
    """
    PHASE 2 STUB: Track resident placements from various sources.
    This is a placeholder for future placement tracking functionality.
    """
    __tablename__ = "placements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Placeholder fields - to be expanded in Phase 2
    status: Mapped[str] = mapped_column(String(50), default="pending")
    source: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Placement(id={self.id}, status='{self.status}')>"

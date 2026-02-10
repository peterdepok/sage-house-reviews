"""
Pydantic schemas for API request/response validation.
Separates API contracts from database models.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from models import ApiType, AlertType, AlertStatus


# ============================================================================
# Platform Schemas
# ============================================================================

class PlatformBase(BaseModel):
    """Base platform schema with common fields."""
    name: str
    base_url: Optional[str] = None
    api_type: ApiType = ApiType.API
    is_active: bool = True


class PlatformCreate(PlatformBase):
    """Schema for creating a new platform."""
    credentials_ref: Optional[str] = None
    config_json: Optional[dict] = None


class PlatformUpdate(BaseModel):
    """Schema for updating a platform."""
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_type: Optional[ApiType] = None
    is_active: Optional[bool] = None
    config_json: Optional[dict] = None


class PlatformResponse(PlatformBase):
    """Schema for platform API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    last_sync: Optional[datetime] = None
    created_at: datetime
    review_count: Optional[int] = None
    average_rating: Optional[float] = None


# ============================================================================
# Review Schemas
# ============================================================================

class ReviewBase(BaseModel):
    """Base review schema."""
    reviewer_name: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_text: Optional[str] = None
    review_date: Optional[datetime] = None


class ReviewCreate(ReviewBase):
    """Schema for creating a review (internal use by scrapers)."""
    platform_id: int
    external_review_id: str
    raw_json: Optional[dict] = None


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""
    response_text: Optional[str] = None
    response_date: Optional[datetime] = None
    needs_response: Optional[bool] = None


class ReviewResponse(ReviewBase):
    """Schema for review API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    platform_id: int
    external_review_id: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    response_text: Optional[str] = None
    response_date: Optional[datetime] = None
    needs_response: bool = False
    created_at: datetime
    platform_name: Optional[str] = None


class ReviewWithPlatform(ReviewResponse):
    """Review response including platform details."""
    platform: Optional[PlatformResponse] = None


class ReviewResponseRequest(BaseModel):
    """Schema for posting a response to a review."""
    response_text: str


# ============================================================================
# Statistics Schemas
# ============================================================================

class PlatformStats(BaseModel):
    """Statistics for a single platform."""
    platform_id: int
    platform_name: str
    total_reviews: int
    average_rating: Optional[float]
    positive_count: int
    negative_count: int
    neutral_count: int
    response_rate: Optional[float]
    last_review_date: Optional[datetime]


class AggregateStats(BaseModel):
    """Aggregate statistics across all platforms."""
    total_reviews: int
    overall_average_rating: Optional[float]
    total_positive: int
    total_negative: int
    total_neutral: int
    overall_response_rate: Optional[float]
    reviews_needing_response: int
    pending_alerts: int
    platforms: List[PlatformStats]


class TrendDataPoint(BaseModel):
    """Single data point for trend analysis."""
    date: datetime
    value: float
    platform_id: Optional[int] = None
    platform_name: Optional[str] = None


class TrendResponse(BaseModel):
    """Response schema for trend endpoints."""
    metric: str
    period: str
    data: List[TrendDataPoint]


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertBase(BaseModel):
    """Base alert schema."""
    alert_type: AlertType
    title: str
    message: Optional[str] = None
    severity: str = "medium"


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    review_id: Optional[int] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    status: Optional[AlertStatus] = None


class AlertResponse(AlertBase):
    """Schema for alert API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    review_id: Optional[int]
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    review: Optional[ReviewResponse] = None


# ============================================================================
# Response Template Schemas
# ============================================================================

class ResponseTemplateBase(BaseModel):
    """Base response template schema."""
    name: str
    category: str
    template_text: str
    variables: Optional[dict] = None


class ResponseTemplateCreate(ResponseTemplateBase):
    """Schema for creating a response template."""
    pass


class ResponseTemplateResponse(ResponseTemplateBase):
    """Schema for response template API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime


# ============================================================================
# Sync Schemas
# ============================================================================

class SyncRequest(BaseModel):
    """Request to trigger a sync operation."""
    platform_ids: Optional[List[int]] = None  # None = sync all


class SyncResult(BaseModel):
    """Result of a sync operation for one platform."""
    platform_id: int
    platform_name: str
    success: bool
    new_reviews: int
    updated_reviews: int
    errors: List[str] = []


class SyncResponse(BaseModel):
    """Response from a sync operation."""
    started_at: datetime
    completed_at: datetime
    results: List[SyncResult]


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    scheduler: str
    timestamp: datetime


# ============================================================================
# Pagination
# ============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

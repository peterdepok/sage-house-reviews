from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class PlatformBase(BaseModel):
    name: str
    base_url: str
    api_type: str

class Platform(PlatformBase):
    id: int
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    platform_id: int
    external_review_id: str
    reviewer_name: str
    rating: float
    review_text: str
    review_date: datetime

class ReviewCreate(ReviewBase):
    raw_json: Optional[Dict[str, Any]] = None

class Review(ReviewBase):
    id: int
    sentiment_score: Optional[float] = None
    response_text: Optional[str] = None
    response_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReviewStats(BaseModel):
    total_reviews: int
    average_rating: float
    rating_breakdown: Dict[int, int]
    sentiment_summary: Dict[str, int]

class Alert(BaseModel):
    id: int
    review_id: int
    alert_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

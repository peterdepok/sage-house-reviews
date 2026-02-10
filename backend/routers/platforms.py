"""
API routes for platform management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Platform, Review
from schemas import PlatformResponse, PlatformCreate, PlatformUpdate


router = APIRouter(prefix="/api/platforms", tags=["platforms"])


@router.get("", response_model=List[PlatformResponse])
def get_platforms(
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False, description="Include inactive platforms"),
):
    """
    Get all platforms with review counts.
    """
    query = db.query(Platform)
    
    if not include_inactive:
        query = query.filter(Platform.is_active == True)
    
    platforms = query.all()
    
    # Get review counts and averages for each platform
    results = []
    for platform in platforms:
        # Count reviews
        review_count = db.query(Review).filter(
            Review.platform_id == platform.id
        ).count()
        
        # Calculate average rating
        avg_rating = db.query(func.avg(Review.rating)).filter(
            Review.platform_id == platform.id,
            Review.rating.isnot(None)
        ).scalar()
        
        response = PlatformResponse.model_validate(platform)
        response.review_count = review_count
        response.average_rating = float(avg_rating) if avg_rating else None
        
        results.append(response)
    
    return results


@router.get("/{platform_id}", response_model=PlatformResponse)
def get_platform(platform_id: int, db: Session = Depends(get_db)):
    """
    Get a single platform by ID.
    """
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    # Get review stats
    review_count = db.query(Review).filter(
        Review.platform_id == platform.id
    ).count()
    
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.platform_id == platform.id,
        Review.rating.isnot(None)
    ).scalar()
    
    response = PlatformResponse.model_validate(platform)
    response.review_count = review_count
    response.average_rating = float(avg_rating) if avg_rating else None
    
    return response


@router.post("", response_model=PlatformResponse)
def create_platform(
    platform_data: PlatformCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new platform.
    """
    # Check for duplicate name
    existing = db.query(Platform).filter(
        Platform.name == platform_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Platform with this name already exists")
    
    platform = Platform(**platform_data.model_dump())
    
    db.add(platform)
    db.commit()
    db.refresh(platform)
    
    return PlatformResponse.model_validate(platform)


@router.patch("/{platform_id}", response_model=PlatformResponse)
def update_platform(
    platform_id: int,
    platform_data: PlatformUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a platform.
    """
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    # Update only provided fields
    update_data = platform_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(platform, field, value)
    
    db.commit()
    db.refresh(platform)
    
    return PlatformResponse.model_validate(platform)


@router.delete("/{platform_id}")
def delete_platform(platform_id: int, db: Session = Depends(get_db)):
    """
    Delete a platform and all its reviews.
    """
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    db.delete(platform)
    db.commit()
    
    return {"message": "Platform deleted", "platform_id": platform_id}


@router.post("/{platform_id}/toggle")
def toggle_platform(platform_id: int, db: Session = Depends(get_db)):
    """
    Toggle a platform's active status.
    """
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    platform.is_active = not platform.is_active
    db.commit()
    
    return {
        "message": f"Platform {'activated' if platform.is_active else 'deactivated'}",
        "platform_id": platform_id,
        "is_active": platform.is_active,
    }

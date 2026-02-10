from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import models, database, schemas
from services import review_service

router = APIRouter()

@router.get("/", response_model=List[schemas.Review])
def get_reviews(db: Session = Depends(database.get_db)):
    return db.query(models.Review).order_by(models.Review.review_date.desc()).all()

@router.get("/stats", response_model=schemas.ReviewStats)
def get_stats(db: Session = Depends(database.get_db)):
    total = db.query(models.Review).count()
    avg_rating = db.query(func.avg(models.Review.rating)).scalar() or 0.0
    
    breakdown = {i: 0 for i in range(1, 6)}
    counts = db.query(models.Review.rating, func.count(models.Review.id)).group_by(models.Review.rating).all()
    for rating, count in counts:
        rounded = int(rating)
        if rounded in breakdown:
            breakdown[rounded] += count

    sentiment = {"positive": 0, "neutral": 0, "negative": 0}
    reviews = db.query(models.Review.sentiment_score).all()
    for (score,) in reviews:
        if score is None: continue
        if score >= 0.05: sentiment["positive"] += 1
        elif score <= -0.05: sentiment["negative"] += 1
        else: sentiment["neutral"] += 1

    return {
        "total_reviews": total,
        "average_rating": round(float(avg_rating), 1),
        "rating_breakdown": breakdown,
        "sentiment_summary": sentiment
    }

@router.post("/sync")
def trigger_sync(background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    platforms = db.query(models.Platform).all()
    for platform in platforms:
        background_tasks.add_task(review_service.sync_platform_reviews, database.SessionLocal(), platform.id)
    return {"message": "Sync started in background"}

@router.post("/{review_id}/response")
def post_response(review_id: int, response_text: str, db: Session = Depends(database.get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.response_text = response_text
    review.response_date = func.now()
    db.commit()
    return {"status": "success"}

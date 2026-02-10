from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, database

router = APIRouter()

@router.get("/")
def get_reviews(db: Session = Depends(database.get_db)):
    return db.query(models.Review).all()

@router.get("/stats")
def get_stats(db: Session = Depends(database.get_db)):
    # Placeholder for aggregate stats
    return {"total": 0, "average_rating": 0.0}

@router.post("/{review_id}/response")
def post_response(review_id: int, response_text: str, db: Session = Depends(database.get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.response_text = response_text
    db.commit()
    return {"status": "success"}

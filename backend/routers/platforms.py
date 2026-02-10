from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, database

router = APIRouter()

@router.get("/")
def get_platforms(db: Session = Depends(database.get_db)):
    return db.query(models.Platform).all()

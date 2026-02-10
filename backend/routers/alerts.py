from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models, database

router = APIRouter()

@router.get("/")
def get_alerts(db: Session = Depends(database.get_db)):
    return db.query(models.Alert).filter(models.Alert.status == "active").all()

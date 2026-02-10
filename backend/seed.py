from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models

def seed_platforms():
    db = SessionLocal()
    platforms = [
        {"name": "Google", "api_type": "api", "base_url": "https://maps.googleapis.com"},
        {"name": "Caring.com", "api_type": "scrape", "base_url": "https://www.caring.com"},
        {"name": "A Place for Mom", "api_type": "scrape", "base_url": "https://www.aplaceformom.com"},
        {"name": "Yelp", "api_type": "api", "base_url": "https://api.yelp.com"},
        {"name": "Facebook", "api_type": "api", "base_url": "https://graph.facebook.com"},
    ]
    
    for p in platforms:
        exists = db.query(models.Platform).filter(models.Platform.name == p["name"]).first()
        if not exists:
            db.add(models.Platform(**p))
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_platforms()
    print("Database seeded with initial platforms.")

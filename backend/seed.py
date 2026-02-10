from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models

def seed_platforms():
    db = SessionLocal()
    platforms = [
        {
            "name": "Google", 
            "api_type": "api", 
            "base_url": "https://maps.googleapis.com",
            "credentials_ref": "ChIJT9G9_AUKK4cR9Z9Z9Z9Z9Z9" # Placeholder Place ID
        },
        {
            "name": "Caring.com", 
            "api_type": "scrape", 
            "base_url": "https://www.caring.com/senior-living/arizona/scottsdale/sage-house-senior-care"
        },
        {
            "name": "A Place for Mom", 
            "api_type": "scrape", 
            "base_url": "https://www.aplaceformom.com/providers/sage-house-senior-care-1457131"
        },
        {
            "name": "Yelp", 
            "api_type": "api", 
            "base_url": "https://www.yelp.com/biz/sage-house-calavar-scottsdale"
        },
        {
            "name": "Facebook", 
            "api_type": "api", 
            "base_url": "https://www.facebook.com/sagehouseaz"
        },
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

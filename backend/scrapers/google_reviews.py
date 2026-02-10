import requests
from typing import List
from .base import BaseScraper, ReviewData
from datetime import datetime
from ..config import settings

class GoogleScraper(BaseScraper):
    def __init__(self, place_id: str):
        self.place_id = place_id
        self.api_key = settings.GOOGLE_PLACES_API_KEY

    def fetch_reviews(self) -> List[ReviewData]:
        if not self.api_key:
            return []
        
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={self.place_id}&fields=reviews&key={self.api_key}"
        response = requests.get(url)
        data = response.json()
        
        results = []
        reviews = data.get("result", {}).get("reviews", [])
        for r in reviews:
            results.append(ReviewData(
                external_id=str(r.get("time")), # Google doesn't always provide a stable ID in public API without additional work
                reviewer_name=r.get("author_name"),
                rating=float(r.get("rating")),
                text=r.get("text"),
                date=datetime.fromtimestamp(r.get("time")),
                raw=r
            ))
        return results

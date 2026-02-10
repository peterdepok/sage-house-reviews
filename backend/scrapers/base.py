from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class ReviewData:
    def __init__(self, external_id: str, reviewer_name: str, rating: float, text: str, date: datetime, raw: Dict[str, Any]):
        self.external_id = external_id
        self.reviewer_name = reviewer_name
        self.rating = rating
        self.text = text
        self.date = date
        self.raw = raw

class BaseScraper(ABC):
    @abstractmethod
    def fetch_reviews(self) -> List[ReviewData]:
        pass

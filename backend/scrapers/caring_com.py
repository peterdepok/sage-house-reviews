import requests
from bs4 import BeautifulSoup
from typing import List
from .base import BaseScraper, ReviewData
from datetime import datetime
import re

class CaringComScraper(BaseScraper):
    def __init__(self, facility_url: str):
        self.facility_url = facility_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_reviews(self) -> List[ReviewData]:
        response = requests.get(self.facility_url, headers=self.headers)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Note: Selectors are based on current Caring.com structure and may need adjustment
        review_elements = soup.select('.review-container, [itemprop="review"]')
        
        for el in review_elements:
            try:
                author = el.select_one('[itemprop="author"], .author-name').get_text(strip=True)
                rating_str = el.select_one('[itemprop="reviewRating"], .rating-stars').get_text(strip=True)
                rating = float(re.search(r'\d+', rating_str).group()) if rating_str else 0
                
                text = el.select_one('[itemprop="reviewBody"], .review-content').get_text(strip=True)
                date_str = el.select_one('[itemprop="datePublished"], .review-date').get_text(strip=True)
                # Attempt to parse date, fallback to now if ambiguous
                try:
                    date = datetime.strptime(date_str, "%b %d, %Y")
                except:
                    date = datetime.now()

                results.append(ReviewData(
                    external_id=f"caring_{hash(text + author)}",
                    reviewer_name=author,
                    rating=rating,
                    text=text,
                    date=date,
                    raw={"source": "caring_com", "raw_date": date_str}
                ))
            except Exception as e:
                print(f"Error parsing Caring.com review: {e}")
                continue
                
        return results

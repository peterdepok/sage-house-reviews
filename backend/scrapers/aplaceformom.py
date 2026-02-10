import requests
from bs4 import BeautifulSoup
from typing import List
from .base import BaseScraper, ReviewData
from datetime import datetime
import re

class APlaceForMomScraper(BaseScraper):
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
        
        # APFM reviews are often inside specific review cards
        review_elements = soup.select('[data-testimonial-id], .review-card')
        
        for el in review_elements:
            try:
                author = el.select_one('.reviewer-name, .author').get_text(strip=True)
                # APFM often uses stars or a numeric value
                rating_el = el.select_one('.rating, .stars')
                rating = 5.0 # Default if not found
                if rating_el:
                    rating_match = re.search(r'\d+', rating_el.get_text())
                    if rating_match:
                        rating = float(rating_match.group())
                
                text = el.select_one('.review-text, .content').get_text(strip=True)
                date_str = el.select_one('.review-date, .date').get_text(strip=True)
                
                try:
                    date = datetime.strptime(date_str, "%m/%d/%Y")
                except:
                    date = datetime.now()

                results.append(ReviewData(
                    external_id=f"apfm_{hash(text + author)}",
                    reviewer_name=author,
                    rating=rating,
                    text=text,
                    date=date,
                    raw={"source": "aplaceformom", "raw_date": date_str}
                ))
            except Exception as e:
                print(f"Error parsing A Place for Mom review: {e}")
                continue
                
        return results

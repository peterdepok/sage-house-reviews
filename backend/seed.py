"""
Database seeding script.
Creates initial platforms and sample data.
"""
import logging
from datetime import datetime

from database import init_db, get_db_context
from models import Platform, ApiType, ResponseTemplate


logger = logging.getLogger(__name__)


def seed_platforms():
    """Create the default platform configurations."""
    
    # Global platforms
    global_platforms = [
        {
            "name": "google",
            "base_url": "https://www.google.com/maps/place/",
            "api_type": ApiType.API,
            "credentials_ref": "GOOGLE_PLACES_API_KEY",
            "config_json": {
                "description": "Google Business Profile reviews via Places API",
                "requires": ["GOOGLE_PLACES_API_KEY", "GOOGLE_PLACE_ID"],
            },
        },
        {
            "name": "yelp",
            "base_url": "https://www.yelp.com/biz/",
            "api_type": ApiType.API,
            "credentials_ref": "YELP_API_KEY",
            "config_json": {
                "description": "Yelp reviews via Fusion API",
                "requires": ["YELP_API_KEY", "YELP_BUSINESS_ID"],
            },
        },
        {
            "name": "facebook",
            "base_url": "https://www.facebook.com/",
            "api_type": ApiType.API,
            "credentials_ref": "FACEBOOK_ACCESS_TOKEN",
            "config_json": {
                "description": "Facebook Page recommendations via Graph API",
                "requires": ["FACEBOOK_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"],
            },
        },
        {
            "name": "senioradvisor",
            "base_url": "https://www.senioradvisor.com/",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "SeniorAdvisor.com reviews via web scraping",
                "requires": ["SENIOR_ADVISOR_URL"],
            },
        },
        {
            "name": "medicare",
            "base_url": "https://www.medicare.gov/care-compare/",
            "api_type": ApiType.API,
            "credentials_ref": None,
            "config_json": {
                "description": "Medicare Care Compare quality ratings",
                "requires": ["MEDICARE_PROVIDER_ID"],
                "note": "Only applicable if facility has Medicare certification",
            },
        },
    ]
    
    # Sage House location-specific platforms
    locations = [
        # Scottsdale (3)
        {
            "name": "sage-house-68th-scottsdale",
            "base_url": "https://www.caring.com/senior-living/arizona/scottsdale/sage-house-68th-street",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - 68th Street (Scottsdale)",
                "location": "Scottsdale, AZ",
                "facility_name": "68th Street",
            },
        },
        {
            "name": "sage-house-calavar-scottsdale",
            "base_url": "https://www.caring.com/senior-living/arizona/scottsdale/sage-house-calavar",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - Calavar (Scottsdale)",
                "location": "Scottsdale, AZ",
                "facility_name": "Calavar",
            },
        },
        {
            "name": "sage-house-crocus-scottsdale",
            "base_url": "https://www.caring.com/senior-living/arizona/scottsdale/sage-house-crocus",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - Crocus (Scottsdale)",
                "location": "Scottsdale, AZ",
                "facility_name": "Crocus",
            },
        },
        # Peoria (1)
        {
            "name": "sage-house-102nd-peoria",
            "base_url": "https://www.caring.com/senior-living/arizona/peoria/sage-house-102nd",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - 102nd (Peoria)",
                "location": "Peoria, AZ",
                "facility_name": "102nd",
            },
        },
        # Phoenix (2)
        {
            "name": "sage-house-expedition-phoenix",
            "base_url": "https://www.caring.com/senior-living/arizona/phoenix/sage-house-expedition",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - Expedition (Phoenix)",
                "location": "Phoenix, AZ",
                "facility_name": "Expedition",
            },
        },
        {
            "name": "sage-house-35th-street-phoenix",
            "base_url": "https://www.caring.com/senior-living/arizona/phoenix/sage-house-35th-street",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - 35th Street (Phoenix)",
                "location": "Phoenix, AZ",
                "facility_name": "35th Street",
            },
        },
        # Glendale (2)
        {
            "name": "sage-house-laurel-i-glendale",
            "base_url": "https://www.caring.com/senior-living/arizona/glendale/sage-house-laurel-i",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - Laurel I (Glendale)",
                "location": "Glendale, AZ",
                "facility_name": "Laurel I",
            },
        },
        {
            "name": "sage-house-laurel-ii-glendale",
            "base_url": "https://www.caring.com/senior-living/arizona/glendale/sage-house-laurel-ii",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Sage House - Laurel II (Glendale)",
                "location": "Glendale, AZ",
                "facility_name": "Laurel II",
            },
        },
    ]
    
    # A Place for Mom and Caring.com as global aggregators
    aggregators = [
        {
            "name": "caring-global",
            "base_url": "https://www.caring.com/",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "Caring.com reviews (global aggregator)",
                "requires": ["CARING_COM_URL"],
            },
        },
        {
            "name": "aplaceformom-global",
            "base_url": "https://www.aplaceformom.com/providers/sage-house-senior-care-1457131",
            "api_type": ApiType.SCRAPE,
            "credentials_ref": None,
            "config_json": {
                "description": "A Place for Mom reviews (global aggregator)",
                "requires": ["A_PLACE_FOR_MOM_URL"],
            },
        },
    ]
    
    all_platforms = global_platforms + locations + aggregators
    
    with get_db_context() as db:
        for platform_data in all_platforms:
            # Check if platform already exists
            existing = db.query(Platform).filter(
                Platform.name == platform_data["name"]
            ).first()
            
            if existing:
                logger.info(f"Platform '{platform_data['name']}' already exists, skipping")
                continue
            
            platform = Platform(**platform_data)
            db.add(platform)
            logger.info(f"Created platform: {platform_data['name']}")
        
        db.commit()
    
    logger.info("Platform seeding completed")


def seed_response_templates():
    """Create default response templates."""
    
    templates = [
        {
            "name": "Thank You - 5 Star",
            "category": "positive",
            "template_text": """Thank you so much for your wonderful review, {reviewer_name}! We're thrilled to hear about your positive experience at Sage House. Our team works hard to provide the best possible care, and feedback like yours means the world to us.

If there's ever anything we can do to make your experience even better, please don't hesitate to reach out.

Warm regards,
The Sage House Team""",
            "variables": {"reviewer_name": "Name of reviewer (or 'valued guest')"},
        },
        {
            "name": "Thank You - 4 Star",
            "category": "positive",
            "template_text": """Thank you for your kind review, {reviewer_name}! We're so glad to hear you had a positive experience at Sage House. We appreciate you taking the time to share your feedback.

We're always looking to improve, so if there's anything that could have made your experience even better, we'd love to hear from you.

Best regards,
The Sage House Team""",
            "variables": {"reviewer_name": "Name of reviewer"},
        },
        {
            "name": "Apologize - Negative Review",
            "category": "negative",
            "template_text": """Dear {reviewer_name},

Thank you for taking the time to share your feedback. We're sorry to hear that your experience didn't meet your expectations, and we take your concerns seriously.

We would very much like to understand more about what happened and work to make things right. Please contact our Community Director at {contact_info} at your earliest convenience so we can discuss this further.

Your feedback helps us improve, and we appreciate you bringing this to our attention.

Sincerely,
The Sage House Team""",
            "variables": {
                "reviewer_name": "Name of reviewer",
                "contact_info": "Phone number or email",
            },
        },
        {
            "name": "Follow Up - Resolved Issue",
            "category": "general",
            "template_text": """Dear {reviewer_name},

Thank you for speaking with us about your concerns. We hope the resolution we discussed addresses your feedback, and we remain committed to providing the highest quality care for our residents.

If you have any additional questions or concerns, please don't hesitate to reach out to us directly.

With appreciation,
The Sage House Team""",
            "variables": {"reviewer_name": "Name of reviewer"},
        },
        {
            "name": "General Thank You",
            "category": "general",
            "template_text": """Thank you for sharing your experience with Sage House, {reviewer_name}. We appreciate all feedback as it helps us continue to improve our services.

If you have any questions or would like to discuss anything further, please feel free to contact us.

Best regards,
The Sage House Team""",
            "variables": {"reviewer_name": "Name of reviewer"},
        },
    ]
    
    with get_db_context() as db:
        for template_data in templates:
            # Check if template already exists
            existing = db.query(ResponseTemplate).filter(
                ResponseTemplate.name == template_data["name"]
            ).first()
            
            if existing:
                logger.info(f"Template '{template_data['name']}' already exists, skipping")
                continue
            
            template = ResponseTemplate(**template_data)
            db.add(template)
            logger.info(f"Created template: {template_data['name']}")
        
        db.commit()
    
    logger.info("Response template seeding completed")


def run_seed():
    """Run all seed functions."""
    logger.info("Starting database seed...")
    
    # Initialize database tables
    init_db()
    
    # Seed data
    seed_platforms()
    seed_response_templates()
    
    logger.info("Database seed completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_seed()

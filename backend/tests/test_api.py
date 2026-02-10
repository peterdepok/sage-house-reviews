"""
API endpoint tests for the Sage House Review Dashboard.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models import Platform, Review, ApiType


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session fixture."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_platform(db_session):
    """Create a sample platform for testing."""
    platform = Platform(
        name="google",
        base_url="https://google.com",
        api_type=ApiType.API,
        is_active=True,
    )
    db_session.add(platform)
    db_session.commit()
    db_session.refresh(platform)
    return platform


@pytest.fixture
def sample_review(db_session, sample_platform):
    """Create a sample review for testing."""
    review = Review(
        platform_id=sample_platform.id,
        external_review_id="test_review_1",
        reviewer_name="John Doe",
        rating=4.5,
        review_text="Great facility, wonderful staff!",
        sentiment_score=0.8,
        sentiment_label="positive",
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "database" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestPlatformEndpoints:
    """Tests for platform management endpoints."""
    
    def test_get_platforms_empty(self, client):
        """Test getting platforms when none exist."""
        response = client.get("/api/platforms")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_platforms(self, client, sample_platform):
        """Test getting list of platforms."""
        response = client.get("/api/platforms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "google"
    
    def test_get_single_platform(self, client, sample_platform):
        """Test getting a single platform."""
        response = client.get(f"/api/platforms/{sample_platform.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "google"
    
    def test_get_platform_not_found(self, client):
        """Test getting non-existent platform."""
        response = client.get("/api/platforms/999")
        assert response.status_code == 404
    
    def test_create_platform(self, client):
        """Test creating a new platform."""
        response = client.post("/api/platforms", json={
            "name": "yelp",
            "base_url": "https://yelp.com",
            "api_type": "api",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "yelp"
        assert data["id"] is not None
    
    def test_toggle_platform(self, client, sample_platform):
        """Test toggling platform active status."""
        response = client.post(f"/api/platforms/{sample_platform.id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False


class TestReviewEndpoints:
    """Tests for review management endpoints."""
    
    def test_get_reviews_empty(self, client, sample_platform):
        """Test getting reviews when none exist."""
        response = client.get("/api/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
    
    def test_get_reviews(self, client, sample_review):
        """Test getting list of reviews."""
        response = client.get("/api/reviews")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["reviewer_name"] == "John Doe"
    
    def test_get_reviews_filtered(self, client, sample_review):
        """Test filtering reviews by sentiment."""
        response = client.get("/api/reviews?sentiment=positive")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        
        response = client.get("/api/reviews?sentiment=negative")
        data = response.json()
        assert data["total"] == 0
    
    def test_get_single_review(self, client, sample_review):
        """Test getting a single review."""
        response = client.get(f"/api/reviews/{sample_review.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["reviewer_name"] == "John Doe"
        assert data["rating"] == 4.5
    
    def test_get_review_not_found(self, client):
        """Test getting non-existent review."""
        response = client.get("/api/reviews/999")
        assert response.status_code == 404
    
    def test_post_review_response(self, client, sample_review):
        """Test posting a response to a review."""
        response = client.post(
            f"/api/reviews/{sample_review.id}/response",
            json={"response_text": "Thank you for your feedback!"}
        )
        assert response.status_code == 200
        
        # Verify response was saved
        response = client.get(f"/api/reviews/{sample_review.id}")
        data = response.json()
        assert data["response_text"] == "Thank you for your feedback!"
    
    def test_get_review_stats(self, client, sample_review):
        """Test getting review statistics."""
        response = client.get("/api/reviews/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_reviews"] == 1
        assert data["total_positive"] == 1
        assert data["total_negative"] == 0


class TestAlertEndpoints:
    """Tests for alert management endpoints."""
    
    def test_get_alerts_empty(self, client):
        """Test getting alerts when none exist."""
        response = client.get("/api/alerts")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_alert_counts(self, client):
        """Test getting alert counts."""
        response = client.get("/api/alerts/counts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestSyncEndpoints:
    """Tests for sync operation endpoints."""
    
    def test_get_sync_status(self, client):
        """Test getting sync status."""
        response = client.get("/api/sync/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "last_sync" in data

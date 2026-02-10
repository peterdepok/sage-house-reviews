"""
Tests for sentiment analysis service.
"""
import pytest
from services.sentiment import SentimentAnalyzer, analyze_sentiment, SentimentLabel


class TestSentimentAnalyzer:
    """Tests for the SentimentAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a VADER analyzer for testing."""
        return SentimentAnalyzer(analyzer_type="vader")
    
    def test_positive_sentiment(self, analyzer):
        """Test detection of positive sentiment."""
        result = analyzer.analyze("This place is wonderful! The staff is amazing and caring.")
        assert result.label == SentimentLabel.POSITIVE
        assert result.score > 0
    
    def test_negative_sentiment(self, analyzer):
        """Test detection of negative sentiment."""
        result = analyzer.analyze("Terrible experience. The food was awful and staff was rude.")
        assert result.label == SentimentLabel.NEGATIVE
        assert result.score < 0
    
    def test_neutral_sentiment(self, analyzer):
        """Test detection of neutral sentiment."""
        result = analyzer.analyze("The facility is located on Main Street.")
        assert result.label == SentimentLabel.NEUTRAL
        assert abs(result.score) < 0.1
    
    def test_empty_text(self, analyzer):
        """Test handling of empty text."""
        result = analyzer.analyze("")
        assert result.label == SentimentLabel.NEUTRAL
        assert result.score == 0.0
    
    def test_rating_adjusted_positive(self, analyzer):
        """Test sentiment with positive rating adjustment."""
        # Neutral text but good rating
        result = analyzer.analyze_rating_adjusted(
            "The facility has many rooms.",
            rating=5.0
        )
        # Should be influenced by rating
        assert result.score > 0
    
    def test_rating_adjusted_negative(self, analyzer):
        """Test sentiment with negative rating adjustment."""
        # Positive text but bad rating
        result = analyzer.analyze_rating_adjusted(
            "Everything was fine.",
            rating=1.0
        )
        # Should be influenced by low rating
        assert result.score < 0.5


class TestConvenienceFunction:
    """Tests for the module-level analyze_sentiment function."""
    
    def test_basic_analysis(self):
        """Test basic sentiment analysis."""
        result = analyze_sentiment("Great service and friendly staff!")
        assert result.label == SentimentLabel.POSITIVE
    
    def test_with_rating(self):
        """Test sentiment analysis with rating."""
        result = analyze_sentiment("It was okay.", rating=4.0)
        assert result.score is not None

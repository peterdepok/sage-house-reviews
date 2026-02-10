"""
Sentiment analysis service for review text.
Supports multiple analyzers: VADER (default) and TextBlob.
"""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from config import settings


logger = logging.getLogger(__name__)


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    score: float  # -1 to 1
    label: SentimentLabel
    confidence: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label.value,
            "confidence": self.confidence,
        }


class SentimentAnalyzer:
    """
    Sentiment analyzer with support for multiple backends.
    
    Supported analyzers:
    - vader: NLTK's VADER (Valence Aware Dictionary and sEntiment Reasoner)
            Best for social media text, handles emojis and slang
    - textblob: TextBlob pattern analyzer
               Good general-purpose sentiment analysis
    """
    
    def __init__(self, analyzer_type: str = None):
        """
        Initialize the sentiment analyzer.
        
        Args:
            analyzer_type: Type of analyzer ('vader' or 'textblob')
        """
        self.analyzer_type = analyzer_type or settings.SENTIMENT_ANALYZER
        self._analyzer = None
        self._initialize_analyzer()
    
    def _initialize_analyzer(self):
        """Initialize the underlying sentiment analyzer."""
        if self.analyzer_type == "vader":
            self._init_vader()
        elif self.analyzer_type == "textblob":
            self._init_textblob()
        else:
            logger.warning(f"Unknown analyzer type '{self.analyzer_type}', falling back to VADER")
            self.analyzer_type = "vader"
            self._init_vader()
    
    def _init_vader(self):
        """Initialize VADER sentiment analyzer."""
        try:
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            import nltk
            
            # Ensure VADER lexicon is downloaded
            try:
                nltk.data.find('sentiment/vader_lexicon.zip')
            except LookupError:
                logger.info("Downloading VADER lexicon...")
                nltk.download('vader_lexicon', quiet=True)
            
            self._analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
            
        except ImportError:
            logger.error("NLTK not installed. Run: pip install nltk")
            raise
    
    def _init_textblob(self):
        """Initialize TextBlob sentiment analyzer."""
        try:
            from textblob import TextBlob
            self._analyzer = TextBlob
            logger.info("TextBlob sentiment analyzer initialized")
            
        except ImportError:
            logger.error("TextBlob not installed. Run: pip install textblob")
            raise
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze the sentiment of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            SentimentResult with score and label
        """
        if not text or not text.strip():
            return SentimentResult(
                score=0.0,
                label=SentimentLabel.NEUTRAL,
                confidence=0.0,
            )
        
        if self.analyzer_type == "vader":
            return self._analyze_vader(text)
        else:
            return self._analyze_textblob(text)
    
    def _analyze_vader(self, text: str) -> SentimentResult:
        """Analyze using VADER."""
        scores = self._analyzer.polarity_scores(text)
        
        # VADER compound score is already -1 to 1
        compound = scores["compound"]
        
        # Determine label based on compound score
        if compound >= 0.05:
            label = SentimentLabel.POSITIVE
        elif compound <= -0.05:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        # Use the dominant sentiment score as confidence
        sentiment_scores = [scores["pos"], scores["neg"], scores["neu"]]
        confidence = max(sentiment_scores)
        
        return SentimentResult(
            score=compound,
            label=label,
            confidence=confidence,
        )
    
    def _analyze_textblob(self, text: str) -> SentimentResult:
        """Analyze using TextBlob."""
        blob = self._analyzer(text)
        
        # TextBlob polarity is -1 to 1
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Determine label
        if polarity > 0.1:
            label = SentimentLabel.POSITIVE
        elif polarity < -0.1:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        return SentimentResult(
            score=polarity,
            label=label,
            confidence=subjectivity,  # How subjective (opinionated) the text is
        )
    
    def analyze_rating_adjusted(
        self, 
        text: str, 
        rating: Optional[float] = None
    ) -> SentimentResult:
        """
        Analyze sentiment with optional rating adjustment.
        
        When a numeric rating is available, we can use it to adjust
        the sentiment score for more accurate results.
        
        Args:
            text: Text to analyze
            rating: Optional numeric rating (1-5 scale)
            
        Returns:
            SentimentResult adjusted by rating
        """
        result = self.analyze(text)
        
        if rating is not None:
            # Normalize rating to -1 to 1 scale
            normalized_rating = (rating - 3) / 2  # 1->-1, 3->0, 5->1
            
            # Weighted average of text sentiment and rating
            # Give more weight to text sentiment when available
            if result.confidence and result.confidence > 0.5:
                adjusted_score = (result.score * 0.7) + (normalized_rating * 0.3)
            else:
                adjusted_score = (result.score * 0.4) + (normalized_rating * 0.6)
            
            # Clamp to -1 to 1
            adjusted_score = max(-1, min(1, adjusted_score))
            
            # Determine label from adjusted score
            if adjusted_score > 0.1:
                label = SentimentLabel.POSITIVE
            elif adjusted_score < -0.1:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            
            return SentimentResult(
                score=adjusted_score,
                label=label,
                confidence=result.confidence,
            )
        
        return result


# Module-level convenience function
_default_analyzer: Optional[SentimentAnalyzer] = None


def analyze_sentiment(
    text: str, 
    rating: Optional[float] = None
) -> SentimentResult:
    """
    Convenience function to analyze sentiment.
    
    Args:
        text: Text to analyze
        rating: Optional rating to factor into sentiment
        
    Returns:
        SentimentResult
    """
    global _default_analyzer
    
    if _default_analyzer is None:
        _default_analyzer = SentimentAnalyzer()
    
    if rating is not None:
        return _default_analyzer.analyze_rating_adjusted(text, rating)
    return _default_analyzer.analyze(text)

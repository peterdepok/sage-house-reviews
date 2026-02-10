from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> float:
    """
    Analyzes text and returns a compound score from -1 (negative) to 1 (positive).
    """
    if not text:
        return 0.0
    
    scores = analyzer.polarity_scores(text)
    return scores['compound']

def get_sentiment_label(score: float) -> str:
    if score >= 0.05:
        return "positive"
    elif score <= -0.05:
        return "negative"
    else:
        return "neutral"

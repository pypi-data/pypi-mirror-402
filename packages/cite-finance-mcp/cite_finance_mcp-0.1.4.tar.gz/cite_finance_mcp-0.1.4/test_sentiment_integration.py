import sys
import os
import asyncio

# Add src to path
sys.path.append(os.getcwd())

from src.intelligence.insights_engine import InsightsEngine, Insight
from src.api.intelligence import get_insights

print("✅ Imports successful.")

async def test_engine():
    engine = InsightsEngine()
    print("✅ InsightsEngine initialized.")
    
    # Mock sentiment data
    mock_sentiment = {
        "social_sentiment": {"overall_score": 0.8},
        "news": [{"sentiment": {"score": 0.9}}]
    }
    
    # Test sentiment analysis method directly
    insights = await engine.analyze_sentiment("TEST", mock_sentiment)
    
    if len(insights) > 0 and insights[0].insight_type == "sentiment":
        print(f"✅ Sentiment analysis working. Generated: {insights[0].title}")
    else:
        print("❌ Sentiment analysis failed to generate insights.")

if __name__ == "__main__":
    asyncio.run(test_engine())

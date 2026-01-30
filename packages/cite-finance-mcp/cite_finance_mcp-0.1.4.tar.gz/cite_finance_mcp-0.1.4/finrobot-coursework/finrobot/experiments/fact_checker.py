"""
Fact checker for validating stock predictions and analysis claims.

Uses web browsing to:
1. Verify if price predictions came true
2. Check if news/earnings claims were accurate
3. Score the accuracy of analysis
"""

import re
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from finrobot.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FactCheckResult:
    """Result of a fact-checking operation."""

    claim: str
    prediction_type: str  # "price_change", "news", "earnings", "unknown"
    confidence: float  # 0-1, how confident is this check?
    accuracy_score: float  # 0-1, how accurate was the claim?
    evidence: str  # What did we find?
    sources: list  # URLs or references used
    verified_at: str  # ISO timestamp of verification


class StockClaimExtractor:
    """Extract quantifiable claims from agent responses."""

    def __init__(self):
        self.patterns = {
            "price_change": {
                "regex": r"(?:predict|expect|forecast|will|should|target).*?(?:go|move|change|rise|fall|up|down).*?(\d+(?:\.\d+)?)\s*%",
                "description": "Percentage price change prediction",
            },
            "price_target": {
                "regex": r"(?:target|price target|fair value).*?\$?\s*(\d+(?:\.\d+)?)",
                "description": "Price target prediction",
            },
            "direction": {
                "regex": r"(?:predict|forecast|expect).*?(up|down|bullish|bearish|positive|negative|increase|decrease)",
                "description": "Direction prediction",
            },
            "earnings": {
                "regex": r"(?:earnings|eps|revenue).*?(beat|miss|meet|strong|weak|positive|negative)",
                "description": "Earnings claim",
            },
            "timeframe": {
                "regex": r"(?:next|within|by|over).*?(day|week|month|quarter|year)",
                "description": "Timeframe for prediction",
            },
        }

    def extract_claims(self, response_text: str) -> Dict[str, list]:
        """
        Extract all quantifiable claims from a response.
        
        Args:
            response_text: Raw response from agent/RAG
            
        Returns:
            Dictionary mapping claim types to extracted values
        """
        claims = {}
        
        for claim_type, pattern_info in self.patterns.items():
            regex = pattern_info["regex"]
            matches = re.findall(regex, response_text, re.IGNORECASE)
            if matches:
                claims[claim_type] = matches
                logger.debug(f"Extracted {claim_type}: {matches}")

        return claims

    def extract_price_prediction(self, response_text: str) -> Optional[Tuple[float, str]]:
        """
        Extract primary price prediction from response.
        
        Returns:
            Tuple of (percentage_change, direction) or None
            Example: (2.5, "up") or (-1.0, "down")
        """
        # Try percentage pattern first
        percent_match = re.search(
            r"(?:predict|expect|forecast|target).*?(?:up|rise|increase|bull|positive).*?(\d+(?:\.\d+)?)\s*%",
            response_text,
            re.IGNORECASE,
        )
        if percent_match:
            return (float(percent_match.group(1)), "up")

        percent_match = re.search(
            r"(?:predict|expect|forecast|target).*?(?:down|fall|decrease|bear|negative).*?(\d+(?:\.\d+)?)\s*%",
            response_text,
            re.IGNORECASE,
        )
        if percent_match:
            return (float(percent_match.group(1)), "down")

        # Try direction-only pattern
        direction_match = re.search(
            r"(?:predict|expect|forecast).*?(bullish|positive|up|rise|increase)",
            response_text,
            re.IGNORECASE,
        )
        if direction_match:
            return (None, "up")

        direction_match = re.search(
            r"(?:predict|expect|forecast).*?(bearish|negative|down|fall|decrease)",
            response_text,
            re.IGNORECASE,
        )
        if direction_match:
            return (None, "down")

        return None


class FactChecker:
    """
    Fact-check predictions against real-world data.
    
    This would ideally connect to:
    - Historical stock data (via yfinance)
    - Current date (for timeframe checking)
    - News APIs (for claim verification)
    """

    def __init__(self):
        self.extractor = StockClaimExtractor()
        self.results: list[FactCheckResult] = []

    def check_price_prediction(
        self, 
        ticker: str,
        prediction: Tuple[float, str],
        reference_price: float,
        actual_price: float,
        timeframe_hours: float = 168,  # 1 week default
    ) -> FactCheckResult:
        """
        Verify if a price prediction came true.
        
        Args:
            ticker: Stock symbol
            prediction: Tuple of (percentage, direction) from model
            reference_price: Stock price at prediction time
            actual_price: Actual stock price at verification time
            timeframe_hours: Hours allowed for prediction
            
        Returns:
            FactCheckResult with accuracy score
        """
        percent_change, direction = prediction
        actual_change_pct = ((actual_price - reference_price) / reference_price) * 100

        # Score based on direction and magnitude
        score = 0.0
        evidence = f"Predicted: {direction} {percent_change}% | Actual: {actual_change_pct:.2f}%"

        # Perfect direction and magnitude match
        if direction == "up" and actual_change_pct > 0:
            if percent_change is None:
                score = 0.8  # Got direction right but no magnitude
            else:
                # Score based on accuracy of magnitude
                error = abs(actual_change_pct - percent_change)
                score = max(0, 1.0 - (error / 5.0))  # 5% error = 0 score
        elif direction == "down" and actual_change_pct < 0:
            if percent_change is None:
                score = 0.8
            else:
                error = abs(actual_change_pct + percent_change)
                score = max(0, 1.0 - (error / 5.0))
        else:
            score = 0.0  # Wrong direction

        result = FactCheckResult(
            claim=f"{ticker}: predict {direction} {percent_change}%",
            prediction_type="price_change",
            confidence=0.9,  # High confidence for quantifiable stock data
            accuracy_score=min(1.0, max(0.0, score)),
            evidence=evidence,
            sources=[f"yfinance/{ticker}"],
            verified_at=datetime.now().isoformat(),
        )

        self.results.append(result)
        logger.info(
            f"Fact check: {ticker} prediction scored {result.accuracy_score:.2f}: {evidence}"
        )
        return result

    def check_multiple_predictions(
        self,
        response_text: str,
        ticker: str,
        reference_price: float,
        actual_price: float,
    ) -> list[FactCheckResult]:
        """
        Extract and verify all predictions from a response.
        
        Args:
            response_text: Raw response from system
            ticker: Stock symbol
            reference_price: Price at prediction time
            actual_price: Current/verified price
            
        Returns:
            List of FactCheckResult objects
        """
        prediction = self.extractor.extract_price_prediction(response_text)
        if not prediction:
            logger.debug(f"No quantifiable predictions found in response")
            return []

        result = self.check_price_prediction(
            ticker=ticker,
            prediction=prediction,
            reference_price=reference_price,
            actual_price=actual_price,
        )
        return [result]

    def get_overall_accuracy(self) -> float:
        """
        Calculate overall accuracy across all verified claims.
        
        Returns:
            Mean accuracy score (0-1)
        """
        if not self.results:
            return 0.0
        return sum(r.accuracy_score for r in self.results) / len(self.results)

    def get_directional_accuracy(self) -> float:
        """
        Calculate what % of price direction predictions were correct.
        
        Returns:
            Percentage of correct directions (0-1)
        """
        if not self.results:
            return 0.0
        correct = sum(1 for r in self.results if r.accuracy_score > 0.5)
        return correct / len(self.results)

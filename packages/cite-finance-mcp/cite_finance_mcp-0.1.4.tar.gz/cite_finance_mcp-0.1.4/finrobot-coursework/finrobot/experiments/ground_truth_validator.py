"""
Ground truth validation system for stock predictions.

Tracks predictions made by systems, waits for the outcome period,
then validates against actual price movements with rigorous accuracy metrics.

Addresses the "no ground truth" criticism by providing verifiable,
quantitative validation of prediction accuracy.
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

import yfinance as yf
import numpy as np

from finrobot.logging import get_logger

logger = get_logger(__name__)


class PredictionType(Enum):
    """Types of predictions that can be validated."""

    PRICE_DIRECTION = "price_direction"  # up/down
    PRICE_TARGET = "price_target"  # specific price
    PERCENT_CHANGE = "percent_change"  # % change
    VOLATILITY = "volatility"  # high/low volatility
    TREND = "trend"  # bullish/bearish trend


@dataclass
class Prediction:
    """A single prediction to be validated."""

    # Identification
    prediction_id: str
    system_name: str  # "agent", "rag", "zeroshot"
    model_name: str  # "gpt-4", "claude-3.5", etc.
    ticker: str
    task_name: str

    # Prediction details
    prediction_type: str
    predicted_value: Any  # Could be "up", 150.5, "10%", etc.
    predicted_direction: Optional[str] = None  # "up" or "down"
    predicted_percent: Optional[float] = None  # Percentage change
    predicted_price: Optional[float] = None  # Target price
    confidence: Optional[float] = None  # 0-1 confidence if stated

    # Timing
    prediction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    validation_timestamp: Optional[str] = None
    timeframe_days: int = 7  # How many days until validation

    # Validation window
    reference_price: float = 0.0  # Price at prediction time
    validation_price: Optional[float] = None  # Price at validation time
    actual_percent_change: Optional[float] = None
    actual_direction: Optional[str] = None

    # Validation results
    is_validated: bool = False
    accuracy_score: float = 0.0  # 0-1 score
    directional_correct: Optional[bool] = None
    magnitude_error: Optional[float] = None  # Absolute error in %

    # Metadata
    response_text: str = ""
    validation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)


@dataclass
class ValidationReport:
    """Aggregated validation report across multiple predictions."""

    system_name: str
    model_name: str
    total_predictions: int
    validated_predictions: int
    pending_predictions: int

    # Accuracy metrics
    overall_accuracy: float  # 0-1
    directional_accuracy: float  # % of correct directions
    mean_magnitude_error: float  # Mean absolute percentage error
    median_magnitude_error: float

    # Performance by prediction type
    accuracy_by_type: Dict[str, float] = field(default_factory=dict)

    # Statistical measures
    confidence_interval_95: Tuple[float, float] = (0.0, 0.0)
    rmse: float = 0.0  # Root mean squared error

    # Breakdown
    correct_predictions: int = 0
    incorrect_predictions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class GroundTruthValidator:
    """
    Comprehensive ground truth validation system.

    Features:
    1. Track predictions with timestamps and reference prices
    2. Automatically validate after timeframe expires
    3. Calculate rigorous accuracy metrics
    4. Generate validation reports with statistical significance
    5. Support multiple prediction types
    6. Handle missing data and edge cases gracefully
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize validator.

        Args:
            storage_dir: Directory to store predictions and validations
        """
        self.storage_dir = Path(storage_dir or "./ground_truth_data")
        self.storage_dir.mkdir(exist_ok=True)
        self.predictions: Dict[str, Prediction] = {}
        self.load_predictions()
        logger.info(f"GroundTruthValidator initialized with {len(self.predictions)} existing predictions")

    def record_prediction(
        self,
        system_name: str,
        model_name: str,
        ticker: str,
        task_name: str,
        response_text: str,
        prediction_type: PredictionType,
        predicted_value: Any,
        timeframe_days: int = 7,
        reference_price: Optional[float] = None,
        confidence: Optional[float] = None,
    ) -> Prediction:
        """
        Record a prediction for later validation.

        Args:
            system_name: System that made prediction
            model_name: Model used
            ticker: Stock symbol
            task_name: Task description
            response_text: Full response text
            prediction_type: Type of prediction
            predicted_value: The predicted value
            timeframe_days: Days until validation
            reference_price: Stock price at prediction time (fetched if None)
            confidence: Stated confidence (0-1)

        Returns:
            Prediction object with unique ID
        """
        # Generate unique ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prediction_id = f"{system_name}_{ticker}_{timestamp}"

        # Fetch reference price if not provided
        if reference_price is None:
            reference_price = self._fetch_current_price(ticker)

        # Parse predicted value
        direction, percent, price = self._parse_prediction(
            predicted_value, prediction_type, reference_price
        )

        prediction = Prediction(
            prediction_id=prediction_id,
            system_name=system_name,
            model_name=model_name,
            ticker=ticker,
            task_name=task_name,
            prediction_type=prediction_type.value,
            predicted_value=predicted_value,
            predicted_direction=direction,
            predicted_percent=percent,
            predicted_price=price,
            confidence=confidence,
            timeframe_days=timeframe_days,
            reference_price=reference_price,
            response_text=response_text,
        )

        self.predictions[prediction_id] = prediction
        self.save_predictions()

        logger.info(
            f"Recorded prediction: {ticker} {direction} {percent}% in {timeframe_days}d "
            f"(ref: ${reference_price:.2f})"
        )

        return prediction

    def _parse_prediction(
        self,
        predicted_value: Any,
        prediction_type: PredictionType,
        reference_price: float,
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        """
        Parse prediction into structured components.

        Returns:
            Tuple of (direction, percent_change, target_price)
        """
        direction = None
        percent = None
        price = None

        if prediction_type == PredictionType.PRICE_DIRECTION:
            direction = str(predicted_value).lower()
            if "up" in direction or "bull" in direction or "positive" in direction:
                direction = "up"
            elif "down" in direction or "bear" in direction or "negative" in direction:
                direction = "down"

        elif prediction_type == PredictionType.PERCENT_CHANGE:
            # Parse percentage
            import re
            match = re.search(r"(-?\d+(?:\.\d+)?)\s*%?", str(predicted_value))
            if match:
                percent = float(match.group(1))
                direction = "up" if percent > 0 else "down"

        elif prediction_type == PredictionType.PRICE_TARGET:
            # Parse price target
            import re
            match = re.search(r"\$?\s*(\d+(?:\.\d+)?)", str(predicted_value))
            if match:
                price = float(match.group(1))
                percent = ((price - reference_price) / reference_price) * 100
                direction = "up" if price > reference_price else "down"

        return direction, percent, price

    def _fetch_current_price(self, ticker: str) -> float:
        """
        Fetch current stock price.

        Args:
            ticker: Stock symbol

        Returns:
            Current price
        """
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
            logger.warning(f"No price data for {ticker}, using 0")
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return 0.0

    def validate_prediction(self, prediction_id: str) -> Prediction:
        """
        Validate a specific prediction against actual outcomes.

        Args:
            prediction_id: ID of prediction to validate

        Returns:
            Updated Prediction with validation results
        """
        if prediction_id not in self.predictions:
            raise ValueError(f"Prediction {prediction_id} not found")

        prediction = self.predictions[prediction_id]

        if prediction.is_validated:
            logger.debug(f"Prediction {prediction_id} already validated")
            return prediction

        # Check if validation window has arrived
        pred_time = datetime.fromisoformat(prediction.prediction_timestamp)
        validation_time = pred_time + timedelta(days=prediction.timeframe_days)

        if datetime.now() < validation_time:
            logger.debug(
                f"Validation window not reached for {prediction_id} "
                f"(due: {validation_time.isoformat()})"
            )
            return prediction

        # Fetch actual price
        actual_price = self._fetch_price_at_date(
            prediction.ticker,
            validation_time
        )

        if actual_price == 0:
            prediction.validation_notes = "Could not fetch validation price"
            return prediction

        # Calculate actual change
        actual_change_pct = (
            (actual_price - prediction.reference_price) / prediction.reference_price
        ) * 100
        actual_direction = "up" if actual_change_pct > 0 else "down"

        prediction.validation_price = actual_price
        prediction.actual_percent_change = actual_change_pct
        prediction.actual_direction = actual_direction
        prediction.validation_timestamp = datetime.now().isoformat()
        prediction.is_validated = True

        # Calculate accuracy metrics
        prediction.directional_correct = (
            prediction.predicted_direction == actual_direction
            if prediction.predicted_direction else None
        )

        if prediction.predicted_percent is not None:
            prediction.magnitude_error = abs(
                actual_change_pct - prediction.predicted_percent
            )

            # Accuracy score: 1.0 for perfect, 0.0 for >10% error
            # Score = max(0, 1 - (error / 10))
            error = prediction.magnitude_error
            base_score = max(0, 1.0 - (error / 10.0))

            # Bonus for correct direction
            direction_bonus = 0.2 if prediction.directional_correct else 0

            prediction.accuracy_score = min(1.0, base_score + direction_bonus)
        elif prediction.directional_correct is not None:
            # Direction-only prediction
            prediction.accuracy_score = 1.0 if prediction.directional_correct else 0.0

        self.save_predictions()

        logger.info(
            f"Validated {prediction_id}: {prediction.ticker} "
            f"predicted {prediction.predicted_direction} {prediction.predicted_percent}%, "
            f"actual {actual_direction} {actual_change_pct:.2f}%, "
            f"score: {prediction.accuracy_score:.3f}"
        )

        return prediction

    def _fetch_price_at_date(self, ticker: str, target_date: datetime) -> float:
        """
        Fetch stock price at specific date.

        Args:
            ticker: Stock symbol
            target_date: Target date

        Returns:
            Price at that date (or nearest available)
        """
        try:
            stock = yf.Ticker(ticker)
            # Fetch a week window around target date
            start = target_date - timedelta(days=3)
            end = target_date + timedelta(days=3)

            data = stock.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

            if data.empty:
                logger.warning(f"No data for {ticker} around {target_date}")
                return 0.0

            # Get closest price to target date
            return float(data['Close'].iloc[-1])

        except Exception as e:
            logger.error(f"Error fetching historical price for {ticker}: {e}")
            return 0.0

    def validate_all_due(self) -> List[Prediction]:
        """
        Validate all predictions whose timeframe has expired.

        Returns:
            List of newly validated predictions
        """
        validated = []

        for prediction_id in list(self.predictions.keys()):
            prediction = self.predictions[prediction_id]

            if prediction.is_validated:
                continue

            pred_time = datetime.fromisoformat(prediction.prediction_timestamp)
            validation_time = pred_time + timedelta(days=prediction.timeframe_days)

            if datetime.now() >= validation_time:
                result = self.validate_prediction(prediction_id)
                if result.is_validated:
                    validated.append(result)

        logger.info(f"Validated {len(validated)} due predictions")
        return validated

    def generate_report(
        self,
        system_filter: Optional[str] = None,
        model_filter: Optional[str] = None,
    ) -> ValidationReport:
        """
        Generate comprehensive validation report.

        Args:
            system_filter: Filter to specific system
            model_filter: Filter to specific model

        Returns:
            ValidationReport with aggregated metrics
        """
        # Filter predictions
        predictions = list(self.predictions.values())

        if system_filter:
            predictions = [p for p in predictions if p.system_name == system_filter]
        if model_filter:
            predictions = [p for p in predictions if p.model_name == model_filter]

        if not predictions:
            logger.warning("No predictions match filters")
            return ValidationReport(
                system_name=system_filter or "all",
                model_name=model_filter or "all",
                total_predictions=0,
                validated_predictions=0,
                pending_predictions=0,
                overall_accuracy=0.0,
                directional_accuracy=0.0,
                mean_magnitude_error=0.0,
                median_magnitude_error=0.0,
            )

        validated = [p for p in predictions if p.is_validated]

        if not validated:
            return ValidationReport(
                system_name=system_filter or "all",
                model_name=model_filter or "all",
                total_predictions=len(predictions),
                validated_predictions=0,
                pending_predictions=len(predictions),
                overall_accuracy=0.0,
                directional_accuracy=0.0,
                mean_magnitude_error=0.0,
                median_magnitude_error=0.0,
            )

        # Calculate metrics
        accuracy_scores = [p.accuracy_score for p in validated]
        directional_correct = [
            p.directional_correct for p in validated
            if p.directional_correct is not None
        ]
        magnitude_errors = [
            p.magnitude_error for p in validated
            if p.magnitude_error is not None
        ]

        overall_accuracy = np.mean(accuracy_scores)
        directional_accuracy = (
            np.mean(directional_correct) if directional_correct else 0.0
        )
        mean_mag_error = np.mean(magnitude_errors) if magnitude_errors else 0.0
        median_mag_error = np.median(magnitude_errors) if magnitude_errors else 0.0

        # Confidence interval (95%)
        if len(accuracy_scores) > 1:
            from scipy import stats
            ci = stats.t.interval(
                0.95,
                len(accuracy_scores) - 1,
                loc=np.mean(accuracy_scores),
                scale=stats.sem(accuracy_scores)
            )
        else:
            ci = (overall_accuracy, overall_accuracy)

        # RMSE
        rmse = np.sqrt(np.mean([e**2 for e in magnitude_errors])) if magnitude_errors else 0.0

        # Accuracy by type
        accuracy_by_type = {}
        for pred_type in set(p.prediction_type for p in validated):
            type_preds = [p for p in validated if p.prediction_type == pred_type]
            accuracy_by_type[pred_type] = np.mean([p.accuracy_score for p in type_preds])

        # Correct/incorrect counts
        correct = sum(1 for p in validated if p.accuracy_score > 0.5)
        incorrect = len(validated) - correct

        report = ValidationReport(
            system_name=system_filter or "all",
            model_name=model_filter or "all",
            total_predictions=len(predictions),
            validated_predictions=len(validated),
            pending_predictions=len(predictions) - len(validated),
            overall_accuracy=float(overall_accuracy),
            directional_accuracy=float(directional_accuracy),
            mean_magnitude_error=float(mean_mag_error),
            median_magnitude_error=float(median_mag_error),
            accuracy_by_type=accuracy_by_type,
            confidence_interval_95=tuple(float(x) for x in ci),
            rmse=float(rmse),
            correct_predictions=correct,
            incorrect_predictions=incorrect,
        )

        return report

    def save_predictions(self):
        """Save all predictions to disk."""
        filepath = self.storage_dir / "predictions.json"
        data = {pid: p.to_dict() for pid, p in self.predictions.items()}

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved {len(self.predictions)} predictions to {filepath}")

    def load_predictions(self):
        """Load predictions from disk."""
        filepath = self.storage_dir / "predictions.json"

        if not filepath.exists():
            return

        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            self.predictions = {
                pid: Prediction(**pdata) for pid, pdata in data.items()
            }

            logger.info(f"Loaded {len(self.predictions)} predictions from {filepath}")

        except Exception as e:
            logger.error(f"Error loading predictions: {e}")

    def export_report_csv(self, filename: Optional[str] = None) -> Path:
        """
        Export validation report to CSV.

        Args:
            filename: Output filename

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}.csv"

        output_path = self.storage_dir / filename

        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(Prediction(
                    prediction_id="", system_name="", model_name="",
                    ticker="", task_name="", prediction_type="",
                    predicted_value=""
                ).to_dict().keys())
            )
            writer.writeheader()

            for prediction in self.predictions.values():
                writer.writerow(prediction.to_dict())

        logger.info(f"Exported validation report to {output_path}")
        return output_path

    def print_summary(self):
        """Print human-readable validation summary."""
        print("\n" + "=" * 80)
        print("GROUND TRUTH VALIDATION SUMMARY")
        print("=" * 80)

        total = len(self.predictions)
        validated = sum(1 for p in self.predictions.values() if p.is_validated)
        pending = total - validated

        print(f"\nTotal Predictions: {total}")
        print(f"Validated: {validated}")
        print(f"Pending: {pending}")

        if validated == 0:
            print("\nNo validated predictions yet.")
            return

        # Per-system reports
        for system in set(p.system_name for p in self.predictions.values()):
            report = self.generate_report(system_filter=system)

            if report.validated_predictions == 0:
                continue

            print(f"\n{system.upper()} System:")
            print(f"  Validated: {report.validated_predictions}/{report.total_predictions}")
            print(f"  Overall Accuracy: {report.overall_accuracy:.3f}")
            print(f"  Directional Accuracy: {report.directional_accuracy:.1%}")
            print(f"  Mean Magnitude Error: {report.mean_magnitude_error:.2f}%")
            print(f"  RMSE: {report.rmse:.2f}%")
            print(f"  95% CI: [{report.confidence_interval_95[0]:.3f}, {report.confidence_interval_95[1]:.3f}]")
            print(f"  Correct: {report.correct_predictions}, Incorrect: {report.incorrect_predictions}")

        print("\n" + "=" * 80)

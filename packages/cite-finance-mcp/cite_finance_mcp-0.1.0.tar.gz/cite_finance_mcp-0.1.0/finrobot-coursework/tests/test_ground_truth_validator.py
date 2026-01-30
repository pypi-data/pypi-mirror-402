"""
Tests for ground truth validation system.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from finrobot.experiments.ground_truth_validator import (
    GroundTruthValidator,
    Prediction,
    PredictionType,
    ValidationReport,
)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def validator(temp_storage_dir):
    """Create validator instance."""
    return GroundTruthValidator(storage_dir=temp_storage_dir)


def test_validator_initialization(validator, temp_storage_dir):
    """Test validator initializes correctly."""
    assert validator.storage_dir == Path(temp_storage_dir)
    assert len(validator.predictions) == 0


def test_record_prediction(validator):
    """Test recording a prediction."""
    prediction = validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="AAPL",
        task_name="price_prediction",
        response_text="I predict AAPL will go up by 5% next week.",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="up 5%",
        reference_price=150.0,
        timeframe_days=7,
    )

    assert prediction.system_name == "agent"
    assert prediction.model_name == "GPT-4"
    assert prediction.ticker == "AAPL"
    assert prediction.predicted_direction == "up"
    assert prediction.predicted_percent == 5.0
    assert prediction.reference_price == 150.0
    assert prediction.is_validated == False

    # Check it's stored
    assert prediction.prediction_id in validator.predictions


def test_prediction_parsing_direction(validator):
    """Test parsing direction-only predictions."""
    prediction = validator.record_prediction(
        system_name="rag",
        model_name="Claude-3.5",
        ticker="MSFT",
        task_name="analysis",
        response_text="Bullish outlook",
        prediction_type=PredictionType.PRICE_DIRECTION,
        predicted_value="bullish",
        reference_price=300.0,
    )

    assert prediction.predicted_direction == "up"


def test_prediction_parsing_percent(validator):
    """Test parsing percentage predictions."""
    prediction = validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="GOOGL",
        task_name="prediction",
        response_text="Down 3.5%",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="-3.5%",
        reference_price=140.0,
    )

    assert prediction.predicted_direction == "down"
    assert prediction.predicted_percent == -3.5


def test_prediction_parsing_price_target(validator):
    """Test parsing price target predictions."""
    prediction = validator.record_prediction(
        system_name="rag",
        model_name="LLaMA",
        ticker="TSLA",
        task_name="target",
        response_text="Price target $250",
        prediction_type=PredictionType.PRICE_TARGET,
        predicted_value="$250",
        reference_price=200.0,
    )

    assert prediction.predicted_price == 250.0
    assert prediction.predicted_direction == "up"
    assert abs(prediction.predicted_percent - 25.0) < 0.1


def test_save_and_load_predictions(validator, temp_storage_dir):
    """Test persistence of predictions."""
    # Record prediction
    validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="NVDA",
        task_name="test",
        response_text="Up 10%",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="10%",
        reference_price=500.0,
    )

    pred_id = list(validator.predictions.keys())[0]

    # Create new validator instance (loads from disk)
    new_validator = GroundTruthValidator(storage_dir=temp_storage_dir)

    assert len(new_validator.predictions) == 1
    assert pred_id in new_validator.predictions
    assert new_validator.predictions[pred_id].ticker == "NVDA"


def test_generate_report_empty(validator):
    """Test report generation with no predictions."""
    report = validator.generate_report()

    assert report.total_predictions == 0
    assert report.validated_predictions == 0
    assert report.overall_accuracy == 0.0


def test_generate_report_with_validations(validator):
    """Test report generation with validated predictions."""
    # Record and manually validate a prediction
    prediction = validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="AAPL",
        task_name="test",
        response_text="Up 2%",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="2%",
        reference_price=150.0,
    )

    # Manually mark as validated with accuracy
    prediction.is_validated = True
    prediction.validation_price = 153.0  # 2% up
    prediction.actual_percent_change = 2.0
    prediction.actual_direction = "up"
    prediction.directional_correct = True
    prediction.magnitude_error = 0.0
    prediction.accuracy_score = 1.0

    validator.predictions[prediction.prediction_id] = prediction

    # Generate report
    report = validator.generate_report(system_filter="agent")

    assert report.total_predictions == 1
    assert report.validated_predictions == 1
    assert report.overall_accuracy == 1.0
    assert report.directional_accuracy == 1.0
    assert report.correct_predictions == 1


def test_generate_report_mixed_accuracy(validator):
    """Test report with both correct and incorrect predictions."""
    # Correct prediction
    pred1 = validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="AAPL",
        task_name="test1",
        response_text="Up 2%",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="2%",
        reference_price=150.0,
    )
    pred1.is_validated = True
    pred1.actual_percent_change = 2.5
    pred1.actual_direction = "up"
    pred1.directional_correct = True
    pred1.magnitude_error = 0.5
    pred1.accuracy_score = 0.9
    validator.predictions[pred1.prediction_id] = pred1

    # Incorrect prediction
    pred2 = validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="MSFT",
        task_name="test2",
        response_text="Up 5%",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="5%",
        reference_price=300.0,
    )
    pred2.is_validated = True
    pred2.actual_percent_change = -2.0
    pred2.actual_direction = "down"
    pred2.directional_correct = False
    pred2.magnitude_error = 7.0
    pred2.accuracy_score = 0.0
    validator.predictions[pred2.prediction_id] = pred2

    # Generate report
    report = validator.generate_report(system_filter="agent")

    assert report.validated_predictions == 2
    assert report.overall_accuracy == 0.45  # (0.9 + 0.0) / 2
    assert report.directional_accuracy == 0.5  # 1/2 correct
    assert report.correct_predictions == 1
    assert report.incorrect_predictions == 1


def test_report_filtering_by_system(validator):
    """Test report filtering by system."""
    # Agent prediction
    pred1 = validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="AAPL",
        task_name="test",
        response_text="Up",
        prediction_type=PredictionType.PRICE_DIRECTION,
        predicted_value="up",
        reference_price=150.0,
    )

    # RAG prediction
    pred2 = validator.record_prediction(
        system_name="rag",
        model_name="GPT-4",
        ticker="MSFT",
        task_name="test",
        response_text="Down",
        prediction_type=PredictionType.PRICE_DIRECTION,
        predicted_value="down",
        reference_price=300.0,
    )

    # Generate agent-only report
    report = validator.generate_report(system_filter="agent")
    assert report.total_predictions == 1
    assert report.system_name == "agent"

    # Generate RAG-only report
    report = validator.generate_report(system_filter="rag")
    assert report.total_predictions == 1
    assert report.system_name == "rag"


def test_export_report_csv(validator, temp_storage_dir):
    """Test CSV export."""
    validator.record_prediction(
        system_name="agent",
        model_name="GPT-4",
        ticker="AAPL",
        task_name="test",
        response_text="Up 2%",
        prediction_type=PredictionType.PERCENT_CHANGE,
        predicted_value="2%",
        reference_price=150.0,
    )

    csv_path = validator.export_report_csv("test_report.csv")
    assert csv_path.exists()
    assert csv_path.name == "test_report.csv"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

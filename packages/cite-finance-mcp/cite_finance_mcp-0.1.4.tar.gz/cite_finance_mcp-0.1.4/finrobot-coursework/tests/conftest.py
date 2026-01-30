"""Pytest configuration and shared fixtures for testing."""

import pytest
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_api_key():
    """Provide mock API keys for testing."""
    return {
        "OPENAI_API_KEY": "test-key-123",
        "FINNHUB_API_KEY": "test-finnhub-123",
        "FMP_API_KEY": "test-fmp-123",
    }


@pytest.fixture
def mock_config_dict():
    """Provide a mock configuration dictionary."""
    return {
        "logging": {
            "level": "DEBUG",
            "format": "json",
            "file": None,
            "max_retries": 3,
        },
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7,
            "timeout": 30,
            "max_tokens": 4096,
        },
        "data_source": {
            "timeout": 10,
            "retries": 3,
            "cache_dir": "/tmp/finrobot_cache",
            "rate_limit": 100,
        },
    }


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def cleanup_env():
    """Clean up environment variables before and after tests."""
    # Save original env
    original_env = os.environ.copy()
    
    yield
    
    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_stock_data():
    """Provide mock stock data for testing."""
    return {
        "AAPL": {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open": [150.0, 151.0, 152.0],
            "high": [152.0, 153.0, 154.0],
            "low": [149.0, 150.0, 151.0],
            "close": [151.0, 152.0, 153.0],
            "volume": [1000000, 1100000, 900000],
        }
    }


@pytest.fixture
def mock_agent_config():
    """Provide mock agent configuration."""
    return {
        "name": "Test_Agent",
        "profile": "Test agent for unit testing",
        "description": "A test agent",
        "toolkits": [],
    }


@pytest.fixture
def mock_workflow_config():
    """Provide mock workflow configuration."""
    return {
        "name": "Test_Workflow",
        "agents": [
            {"name": "Agent1", "profile": "First test agent"},
            {"name": "Agent2", "profile": "Second test agent"},
        ],
    }

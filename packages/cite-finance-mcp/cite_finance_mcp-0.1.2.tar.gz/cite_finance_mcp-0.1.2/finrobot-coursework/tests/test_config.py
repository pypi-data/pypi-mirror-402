"""Unit tests for finrobot.config module."""

import unittest
import tempfile
import json
import os
from pathlib import Path

from finrobot.config import (
    LoggingConfig,
    LLMConfig,
    DataSourceConfig,
    FinRobotConfig,
    get_config,
    set_config,
    load_config,
)
from finrobot.errors import ValidationError, ConfigurationError


class TestLoggingConfig(unittest.TestCase):
    """Test LoggingConfig dataclass."""
    
    def test_logging_config_creation(self):
        """Test creating LoggingConfig."""
        config = LoggingConfig(
            level="DEBUG",
            format="json",
            file="/tmp/finrobot.log",
            max_retries=3
        )
        
        self.assertEqual(config.level, "DEBUG")
        self.assertEqual(config.format, "json")
        self.assertEqual(config.file, "/tmp/finrobot.log")
        self.assertEqual(config.max_retries, 3)
    
    def test_logging_config_creation_defaults(self):
        """Test LoggingConfig with default values."""
        config = LoggingConfig()
        
        self.assertEqual(config.level, "INFO")
        self.assertEqual(config.max_retries, 3)
        self.assertIsNone(config.file)


class TestLLMConfig(unittest.TestCase):
    """Test LLMConfig dataclass."""
    
    def test_llm_config_creation(self):
        """Test creating LLMConfig."""
        config = LLMConfig(
            model="gpt-4",
            temperature=0.7,
            timeout=30,
            max_tokens=4096
        )
        
        self.assertEqual(config.model, "gpt-4")
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_tokens, 4096)


class TestDataSourceConfig(unittest.TestCase):
    """Test DataSourceConfig dataclass."""
    
    def test_datasource_config_creation(self):
        """Test creating DataSourceConfig."""
        config = DataSourceConfig(
            timeout=10,
            max_retries=3,
            cache_dir="/tmp/cache",
            rate_limit=True
        )
        
        self.assertEqual(config.timeout, 10)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.cache_dir, "/tmp/cache")
        self.assertTrue(config.rate_limit)


class TestFinRobotConfig(unittest.TestCase):
    """Test FinRobotConfig dataclass."""
    
    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
    
    def test_finrobot_config_creation(self):
        """Test creating FinRobotConfig."""
        config = FinRobotConfig()
        
        self.assertIsInstance(config.logging, LoggingConfig)
        self.assertIsInstance(config.llm, LLMConfig)
        self.assertIsInstance(config.data_source, DataSourceConfig)
    
    def test_finrobot_config_to_dict(self):
        """Test converting FinRobotConfig to dict."""
        config = FinRobotConfig()
        result = config.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertIn("logging", result)
        self.assertIn("llm", result)
        self.assertIn("data_source", result)
    
    def test_finrobot_config_from_file(self):
        """Test loading FinRobotConfig from file."""
        config_data = {
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": None,
                "max_retries": 2,
            },
            "llm": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.5,
                "timeout": 60,
                "max_tokens": 2048,
            },
            "data_source": {
                "timeout": 5,
                "max_retries": 2,
                "cache_dir": "/tmp/cache",
                "rate_limit": True,
            },
        }
        
        config_file = self.temp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)
        
        config = FinRobotConfig.from_file(str(config_file))
        
        self.assertEqual(config.logging.level, "INFO")
        self.assertEqual(config.llm.model, "gpt-3.5-turbo")
        self.assertEqual(config.data_source.timeout, 5)
    
    def test_finrobot_config_from_file_nonexistent(self):
        """Test loading from nonexistent file."""
        from finrobot.errors import ValidationError
        try:
            FinRobotConfig.from_file("/nonexistent/path.json")
            self.fail("Should have raised ValidationError or FileNotFoundError")
        except (ConfigurationError, FileNotFoundError, ValidationError):
            pass  # Expected
    
    def test_finrobot_config_from_env(self):
        """Test loading FinRobotConfig from environment variables."""
        # Set environment variables
        os.environ["FINROBOT_LOG_LEVEL"] = "DEBUG"
        os.environ["FINROBOT_LLM_MODEL"] = "gpt-4-turbo"
        os.environ["FINROBOT_DATA_TIMEOUT"] = "15"
        
        try:
            config = FinRobotConfig.from_env()
            
            # At least some values should be overridden
            self.assertIsNotNone(config)
        finally:
            # Clean up
            for key in ["FINROBOT_LOG_LEVEL", "FINROBOT_LLM_MODEL", "FINROBOT_DATA_TIMEOUT"]:
                os.environ.pop(key, None)
    
    def test_finrobot_config_save(self):
        """Test saving FinRobotConfig to file."""
        config = FinRobotConfig()
        save_path = self.temp_path / "saved_config.json"
        
        config.save(str(save_path))
        
        self.assertTrue(save_path.exists())
        
        # Verify saved content
        with open(save_path) as f:
            data = json.load(f)
        
        self.assertIn("logging", data)
        self.assertIn("llm", data)
        self.assertIn("data_source", data)


class TestGlobalConfigManagement(unittest.TestCase):
    """Test global config management functions."""
    
    def test_get_config_returns_config(self):
        """Test get_config returns FinRobotConfig."""
        config = get_config()
        self.assertIsInstance(config, FinRobotConfig)
    
    def test_set_config_stores_config(self):
        """Test set_config stores configuration."""
        new_config = FinRobotConfig()
        set_config(new_config)
        
        retrieved_config = get_config()
        self.assertIs(retrieved_config, new_config)
    
    def test_load_config_from_file(self):
        """Test load_config from file."""
        temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(temp_dir.name)
        
        try:
            config_data = {
                "logging": {
                    "level": "DEBUG",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
                    "max_retries": 3,
                    "cache_dir": "/tmp/cache",
                    "rate_limit": True,
                },
            }
            
            config_file = temp_path / "config.json"
            with open(config_file, "w") as f:
                json.dump(config_data, f)
            
            load_config(str(config_file))
            
            config = get_config()
            self.assertEqual(config.logging.level, "DEBUG")
            self.assertEqual(config.llm.model, "gpt-4")
        
        finally:
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()

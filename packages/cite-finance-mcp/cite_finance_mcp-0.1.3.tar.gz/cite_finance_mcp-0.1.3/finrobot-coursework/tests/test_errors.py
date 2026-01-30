"""Unit tests for finrobot.errors module."""

import unittest
from finrobot.errors import (
    FinRobotException,
    ConfigurationError,
    DataSourceError,
    APIError,
    RateLimitError,
    TimeoutError as FinRobotTimeoutError,
    AgentError,
    ToolError,
    ValidationError,
    retry_with_backoff,
    handle_errors,
    validate_arguments,
    ErrorHandler,
)


class TestFinRobotException(unittest.TestCase):
    """Test FinRobotException base class."""
    
    def test_exception_creation(self):
        """Test creating a FinRobotException."""
        exc = FinRobotException("Test error", "TEST_CODE", {"key": "value"})
        self.assertEqual(exc.message, "Test error")
        self.assertEqual(exc.code, "TEST_CODE")
        self.assertEqual(exc.details, {"key": "value"})
    
    def test_exception_to_dict(self):
        """Test converting exception to dictionary."""
        exc = FinRobotException("Test error", "TEST_CODE", {"key": "value"})
        result = exc.to_dict()
        
        self.assertEqual(result["error_type"], "FinRobotException")
        self.assertEqual(result["code"], "TEST_CODE")
        self.assertEqual(result["message"], "Test error")
        self.assertEqual(result["details"], {"key": "value"})


class TestCustomExceptions(unittest.TestCase):
    """Test custom exception classes."""
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError("Bad config", {"field": "api_key"})
        self.assertEqual(exc.code, "CONFIG_ERROR")
        self.assertIn("field", exc.details)
    
    def test_data_source_error(self):
        """Test DataSourceError."""
        exc = DataSourceError("Data fetch failed")
        self.assertEqual(exc.code, "DATASOURCE_ERROR")
    
    def test_api_error(self):
        """Test APIError."""
        exc = APIError("API call failed", status_code=500)
        self.assertEqual(exc.code, "API_ERROR")
        self.assertEqual(exc.details["status_code"], 500)
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        exc = RateLimitError("Rate limited", retry_after=60)
        self.assertEqual(exc.code, "RATE_LIMIT_ERROR")
        self.assertEqual(exc.details["retry_after"], 60)
    
    def test_timeout_error(self):
        """Test TimeoutError."""
        exc = FinRobotTimeoutError("Operation timed out", timeout_seconds=30.0)
        self.assertEqual(exc.code, "TIMEOUT_ERROR")
        self.assertEqual(exc.details["timeout_seconds"], 30.0)
    
    def test_agent_error(self):
        """Test AgentError."""
        exc = AgentError("Agent failed", agent_name="TestAgent")
        self.assertEqual(exc.code, "AGENT_ERROR")
        self.assertEqual(exc.details["agent_name"], "TestAgent")
    
    def test_tool_error(self):
        """Test ToolError."""
        exc = ToolError("Tool execution failed", tool_name="test_tool")
        self.assertEqual(exc.code, "TOOL_ERROR")
        self.assertEqual(exc.details["tool_name"], "test_tool")
    
    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Invalid value", field="email")
        self.assertEqual(exc.code, "VALIDATION_ERROR")
        self.assertEqual(exc.details["field"], "email")


class TestRetryDecorator(unittest.TestCase):
    """Test retry_with_backoff decorator."""
    
    def test_retry_success_first_attempt(self):
        """Test successful call on first attempt."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3)
        def succeed():
            call_count[0] += 1
            return "success"
        
        result = succeed()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 1)
    
    def test_retry_eventual_success(self):
        """Test successful call after retries."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def eventually_succeed():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = eventually_succeed()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 3)
    
    def test_retry_max_retries_exceeded(self):
        """Test failure after max retries."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_fail():
            call_count[0] += 1
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError):
            always_fail()
        
        self.assertEqual(call_count[0], 3)  # Initial + 2 retries


class TestErrorHandlerDecorator(unittest.TestCase):
    """Test handle_errors decorator."""
    
    def test_handle_errors_success(self):
        """Test decorator with successful function."""
        @handle_errors(default_return=None)
        def succeed():
            return "success"
        
        result = succeed()
        self.assertEqual(result, "success")
    
    def test_handle_errors_suppress_exception(self):
        """Test decorator suppressing exception."""
        @handle_errors(default_return="default")
        def fail():
            raise ValueError("Test error")
        
        result = fail()
        self.assertEqual(result, "default")
    
    def test_handle_errors_reraise_exception(self):
        """Test decorator reraising exception."""
        @handle_errors(reraise=True)
        def fail():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            fail()


class TestValidateArgumentsDecorator(unittest.TestCase):
    """Test validate_arguments decorator."""
    
    def test_validate_arguments_success(self):
        """Test with valid arguments."""
        @validate_arguments(age=lambda x: isinstance(x, int) and x >= 0)
        def set_age(age):
            return age
        
        result = set_age(age=25)
        self.assertEqual(result, 25)
    
    def test_validate_arguments_failure(self):
        """Test with invalid arguments."""
        @validate_arguments(age=lambda x: isinstance(x, int) and x >= 0)
        def set_age(age):
            return age
        
        with self.assertRaises(ValidationError):
            set_age(age=-5)
    
    def test_validate_arguments_multiple(self):
        """Test with multiple validators."""
        @validate_arguments(
            name=lambda x: isinstance(x, str) and len(x) > 0,
            age=lambda x: isinstance(x, int) and x >= 0
        )
        def create_person(name, age):
            return (name, age)
        
        result = create_person(name="John", age=30)
        self.assertEqual(result, ("John", 30))
        
        with self.assertRaises(ValidationError):
            create_person(name="", age=30)


class TestErrorHandler(unittest.TestCase):
    """Test ErrorHandler context manager."""
    
    def test_error_handler_success(self):
        """Test context manager with successful operation."""
        with ErrorHandler("test_operation") as handler:
            result = 10 + 20
        
        self.assertIsNone(handler.exception)
    
    def test_error_handler_suppress_exception(self):
        """Test context manager suppressing exception."""
        with ErrorHandler("test_operation", reraise=False) as handler:
            raise ValueError("Test error")
        
        self.assertIsInstance(handler.exception, ValueError)
    
    def test_error_handler_reraise_exception(self):
        """Test context manager reraising exception."""
        with self.assertRaises(ValueError):
            with ErrorHandler("test_operation", reraise=True):
                raise ValueError("Test error")


if __name__ == "__main__":
    unittest.main()

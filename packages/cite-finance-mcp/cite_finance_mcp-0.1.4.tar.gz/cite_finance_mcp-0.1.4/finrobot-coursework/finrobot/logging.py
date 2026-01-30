"""
Comprehensive logging system for FinRobot.

Provides structured logging, metrics tracking, and performance monitoring.
"""

import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Log levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra'):
            log_obj.update(record.extra)
        
        return json.dumps(log_obj)


class FinRobotLogger:
    """Central logging system for FinRobot"""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.root_logger = logging.getLogger('finrobot')
        self._configured = False
    
    def setup(self, level: str = "INFO", log_file: Optional[str] = None) -> None:
        """
        Setup logging system.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file to write logs to
        """
        if self._configured:
            return
        
        # Set root logger level
        self.root_logger.setLevel(getattr(logging, level))
        
        # Remove existing handlers
        self.root_logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.root_logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level))
            file_formatter = JSONFormatter()
            file_handler.setFormatter(file_formatter)
            self.root_logger.addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get logger for a module"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(f'finrobot.{name}')
        return self._loggers[name]


# Singleton instance
_logger_instance = FinRobotLogger()


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup global logging"""
    _logger_instance.setup(level, log_file)


def get_logger(name: str) -> logging.Logger:
    """Get logger for a module"""
    return _logger_instance.get_logger(name)


class MetricsCollector:
    """Collect metrics for evaluation"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.logger = get_logger('metrics')
    
    def record(self, key: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric"""
        metric_entry = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'tags': tags or {}
        }
        
        if key not in self.metrics:
            self.metrics[key] = []
        
        self.metrics[key].append(metric_entry)
        
        self.logger.debug(
            f"Recorded metric: {key}={value}",
            extra={'metric': metric_entry}
        )
    
    def get(self, key: str) -> list:
        """Get metrics for a key"""
        return self.metrics.get(key, [])
    
    def get_latest(self, key: str) -> Optional[Any]:
        """Get latest metric value"""
        values = self.get(key)
        return values[-1]['value'] if values else None
    
    def save(self, path: str) -> None:
        """Save metrics to JSON file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        self.logger.info(f"Metrics saved to {path}")
    
    def clear(self) -> None:
        """Clear all metrics"""
        self.metrics.clear()


# Global metrics instance
_metrics = MetricsCollector()


def record_metric(key: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
    """Record a metric"""
    _metrics.record(key, value, tags)


def get_metrics() -> MetricsCollector:
    """Get global metrics collector"""
    return _metrics

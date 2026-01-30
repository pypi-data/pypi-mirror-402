"""
Configuration management for FinRobot.

This module handles all configuration settings with proper validation
and environment variable support.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_retries: int = 3


@dataclass
class LLMConfig:
    """LLM configuration"""
    model: str = "gpt-4-0125-preview"
    temperature: float = 0.0
    timeout: int = 120
    max_tokens: Optional[int] = None


@dataclass
class DataSourceConfig:
    """Data source configuration"""
    timeout: int = 30
    max_retries: int = 3
    cache_dir: str = ".cache"
    rate_limit: bool = True


@dataclass
class FinRobotConfig:
    """Main FinRobot configuration"""
    logging: LoggingConfig = None
    llm: LLMConfig = None
    data_source: DataSourceConfig = None
    work_dir: str = "finrobot_work"
    debug: bool = False
    
    def __post_init__(self):
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.llm is None:
            self.llm = LLMConfig()
        if self.data_source is None:
            self.data_source = DataSourceConfig()
    
    @classmethod
    def from_file(cls, config_path: str) -> "FinRobotConfig":
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Parse nested configs
        logging_config = LoggingConfig(**config_dict.get('logging', {}))
        llm_config = LLMConfig(**config_dict.get('llm', {}))
        data_source_config = DataSourceConfig(**config_dict.get('data_source', {}))
        
        return cls(
            logging=logging_config,
            llm=llm_config,
            data_source=data_source_config,
            work_dir=config_dict.get('work_dir', 'finrobot_work'),
            debug=config_dict.get('debug', False)
        )
    
    @classmethod
    def from_env(cls) -> "FinRobotConfig":
        """Load configuration from environment variables"""
        return cls(
            logging=LoggingConfig(
                level=os.getenv('FINROBOT_LOG_LEVEL', 'INFO'),
                file=os.getenv('FINROBOT_LOG_FILE')
            ),
            llm=LLMConfig(
                model=os.getenv('FINROBOT_MODEL', 'gpt-4-0125-preview'),
                temperature=float(os.getenv('FINROBOT_TEMPERATURE', '0.0')),
                timeout=int(os.getenv('FINROBOT_TIMEOUT', '120'))
            ),
            debug=os.getenv('FINROBOT_DEBUG', 'false').lower() == 'true'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'logging': asdict(self.logging),
            'llm': asdict(self.llm),
            'data_source': asdict(self.data_source),
            'work_dir': self.work_dir,
            'debug': self.debug
        }
    
    def save(self, path: str) -> None:
        """Save configuration to JSON file"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Global config instance
_config: Optional[FinRobotConfig] = None


def get_config() -> FinRobotConfig:
    """Get global configuration"""
    global _config
    if _config is None:
        _config = FinRobotConfig()
    return _config


def set_config(config: FinRobotConfig) -> None:
    """Set global configuration"""
    global _config
    _config = config


def load_config(path: str) -> FinRobotConfig:
    """Load and set configuration from file"""
    config = FinRobotConfig.from_file(path)
    set_config(config)
    return config


def load_config_from_env() -> FinRobotConfig:
    """Load and set configuration from environment"""
    config = FinRobotConfig.from_env()
    set_config(config)
    return config

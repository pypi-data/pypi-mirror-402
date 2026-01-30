import os
import json
import logging
import pandas as pd
from datetime import date, timedelta, datetime
from typing import Annotated, Optional, Any, Dict, Union
from pathlib import Path

from finrobot.errors import ValidationError, FinRobotException


logger = logging.getLogger('finrobot.utils')


# Define custom annotated types
# VerboseType = Annotated[bool, "Whether to print data to console. Default to True."]
SavePathType = Annotated[Optional[str], "File path to save data. If None, data is not saved."]


# def process_output(data: pd.DataFrame, tag: str, verbose: VerboseType = True, save_path: SavePathType = None) -> None:
#     if verbose:
#         print(data.to_string())
#     if save_path:
#         data.to_csv(save_path)
#         print(f"{tag} saved to {save_path}")


def save_output(
    data: Union[pd.DataFrame, Dict, list],
    tag: str,
    save_path: SavePathType = None
) -> None:
    """
    Save output data to file.
    
    Args:
        data: DataFrame, dictionary, or list to save
        tag: Tag/description for logging
        save_path: Path to save file. If None, no save occurs.
    
    Raises:
        ValidationError: If data is invalid or path is invalid
    """
    if save_path is None:
        logger.debug(f"No save path provided for {tag}, skipping save")
        return
    
    try:
        # Validate inputs
        if not isinstance(tag, str) or not tag:
            raise ValidationError("Tag must be a non-empty string", field="tag")
        
        # Create parent directories if needed
        save_path_obj = Path(save_path)
        save_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle different data types
        if isinstance(data, pd.DataFrame):
            data.to_csv(save_path)
            logger.info(f"{tag} saved to {save_path} ({len(data)} rows)")
        elif isinstance(data, dict):
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"{tag} saved to {save_path}")
        elif isinstance(data, list):
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"{tag} saved to {save_path}")
        else:
            raise ValidationError(
                f"Unsupported data type: {type(data).__name__}",
                field="data"
            )
    
    except Exception as e:
        logger.error(f"Failed to save {tag} to {save_path}: {str(e)}")
        raise


def get_current_date() -> str:
    """
    Get current date as string.
    
    Returns:
        Current date in YYYY-MM-DD format
    """
    try:
        current_date = date.today().strftime("%Y-%m-%d")
        logger.debug(f"Current date: {current_date}")
        return current_date
    except Exception as e:
        logger.error(f"Failed to get current date: {str(e)}")
        raise


def register_keys_from_json(file_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load API keys and environment variables from JSON file.
    
    Args:
        file_path: Path to JSON file with key-value pairs
    
    Returns:
        Dictionary of loaded keys
    
    Raises:
        ValidationError: If file doesn't exist or is invalid JSON
    """
    try:
        file_path = Path(file_path)
        
        # Validate file exists and is readable
        if not file_path.exists():
            raise ValidationError(
                f"Config file not found: {file_path}",
                field="file_path"
            )
        
        if not file_path.is_file():
            raise ValidationError(
                f"Path is not a file: {file_path}",
                field="file_path"
            )
        
        # Load and parse JSON
        with open(file_path, "r") as f:
            keys = json.load(f)
        
        if not isinstance(keys, dict):
            raise ValidationError(
                "JSON file must contain a dictionary/object",
                field="file_path"
            )
        
        # Register environment variables
        registered_keys = {}
        for key, value in keys.items():
            if not isinstance(key, str):
                logger.warning(f"Skipping non-string key: {key}")
                continue
            
            if value is None:
                logger.warning(f"Skipping None value for key: {key}")
                continue
            
            os.environ[key] = str(value)
            registered_keys[key] = str(value)
            logger.debug(f"Registered environment variable: {key}")
        
        logger.info(f"Loaded {len(registered_keys)} keys from {file_path}")
        return registered_keys
    
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"Invalid JSON in {file_path}: {str(e)}",
            field="file_path"
        )
    except Exception as e:
        logger.error(f"Failed to register keys from {file_path}: {str(e)}")
        raise


def decorate_all_methods(decorator):
    """
    Decorator factory to apply a decorator to all methods of a class.
    
    Args:
        decorator: Decorator function to apply
    
    Returns:
        Class decorator function
    """
    def class_decorator(cls):
        try:
            for attr_name, attr_value in cls.__dict__.items():
                if callable(attr_value) and not attr_name.startswith('_'):
                    setattr(cls, attr_name, decorator(attr_value))
            
            logger.debug(f"Applied decorator to all methods of {cls.__name__}")
            return cls
        except Exception as e:
            logger.error(f"Failed to decorate class {cls.__name__}: {str(e)}")
            raise

    return class_decorator


def get_next_weekday(input_date: Union[str, datetime]) -> datetime:
    """
    Get next weekday from given date (skip weekends).
    
    Args:
        input_date: Date as string (YYYY-MM-DD) or datetime object
    
    Returns:
        Next weekday as datetime object
    
    Raises:
        ValidationError: If date format is invalid
    """
    try:
        # Parse date if string
        if isinstance(input_date, str):
            try:
                dt = datetime.strptime(input_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValidationError(
                    f"Invalid date format. Expected YYYY-MM-DD, got: {input_date}",
                    field="input_date"
                )
        elif isinstance(input_date, datetime):
            dt = input_date
        elif isinstance(input_date, date):
            dt = datetime.combine(input_date, datetime.min.time())
        else:
            raise ValidationError(
                f"Date must be string or datetime, got: {type(input_date).__name__}",
                field="input_date"
            )
        
        # If already a weekday, return it
        if dt.weekday() < 5:  # 0-4 are Monday-Friday
            logger.debug(f"Date {dt.strftime('%Y-%m-%d')} is already a weekday")
            return dt
        
        # Skip to next Monday
        days_to_add = 7 - dt.weekday()
        next_weekday = dt + timedelta(days=days_to_add)
        logger.debug(f"Moved from {dt.strftime('%Y-%m-%d')} to {next_weekday.strftime('%Y-%m-%d')}")
        return next_weekday
    
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Failed to get next weekday for {input_date}: {str(e)}")
        raise


# def create_inner_assistant(
#         name, system_message, llm_config, max_round=10,
#         code_execution_config=None
#     ):

#     inner_assistant = autogen.AssistantAgent(
#         name=name,
#         system_message=system_message + "Reply TERMINATE when the task is done.",
#         llm_config=llm_config,
#         is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
#     )
#     executor = autogen.UserProxyAgent(
#         name=f"{name}-executor",
#         human_input_mode="NEVER",
#         code_execution_config=code_execution_config,
#         default_auto_reply="",
#         is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
#     )
#     assistant.register_nested_chats(
#         [{"recipient": assistant, "message": reflection_message, "summary_method": "last_msg", "max_turns": 1}],
#         trigger=ConversableAgent
#         )
#     return manager

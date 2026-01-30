"""
Error handling and exceptions for FinRobot.

Provides custom exception classes and error handling utilities.
"""

import logging
from typing import Optional, Type, Any
from functools import wraps
import traceback


logger = logging.getLogger('finrobot.errors')


class FinRobotException(Exception):
    """Base exception for FinRobot"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary"""
        return {
            'error_type': self.__class__.__name__,
            'code': self.code,
            'message': self.message,
            'details': self.details
        }


class ConfigurationError(FinRobotException):
    """Configuration-related error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class DataSourceError(FinRobotException):
    """Data source-related error"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, "DATASOURCE_ERROR", details)


class APIError(FinRobotException):
    """API-related error"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if status_code is not None:
            details['status_code'] = status_code
        super().__init__(message, "API_ERROR", details)


class RateLimitError(APIError):
    """Rate limit error"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        details = {}
        if retry_after is not None:
            details['retry_after'] = retry_after
        super().__init__(message, details=details)
        self.code = "RATE_LIMIT_ERROR"


class TimeoutError(FinRobotException):
    """Timeout error"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        details = {}
        if timeout_seconds is not None:
            details['timeout_seconds'] = timeout_seconds
        super().__init__(message, "TIMEOUT_ERROR", details)


class AgentError(FinRobotException):
    """Agent-related error"""
    
    def __init__(self, message: str, agent_name: Optional[str] = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if agent_name is not None:
            details['agent_name'] = agent_name
        super().__init__(message, "AGENT_ERROR", details)


class ToolError(FinRobotException):
    """Tool execution error"""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if tool_name is not None:
            details['tool_name'] = tool_name
        super().__init__(message, "TOOL_ERROR", details)


class ValidationError(FinRobotException):
    """Validation error"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[dict] = None):
        if details is None:
            details = {}
        if field is not None:
            details['field'] = field
        super().__init__(message, "VALIDATION_ERROR", details)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        backoff_factor: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}")
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Failed after {max_retries + 1} attempts: {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}, "
                        f"retrying in {delay}s. Error: {str(e)}"
                    )
                    
                    import time
                    time.sleep(delay)
                    delay *= backoff_factor
        
        return wrapper
    return decorator


def handle_errors(
    default_return: Any = None,
    reraise: bool = False,
    log_level: str = 'ERROR'
):
    """
    Decorator for handling errors gracefully.
    
    Args:
        default_return: Value to return on error
        reraise: Whether to reraise the exception
        log_level: Logging level for the error
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, log_level.lower(), logger.error)
                log_func(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def validate_arguments(**validators):
    """
    Decorator for validating function arguments.
    
    Args:
        **validators: Mapping of argument names to validator functions
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate kwargs
            for arg_name, validator in validators.items():
                if arg_name in kwargs:
                    value = kwargs[arg_name]
                    if not validator(value):
                        raise ValidationError(
                            f"Invalid value for argument '{arg_name}': {value}",
                            field=arg_name
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class ErrorHandler:
    """Context manager for error handling"""
    
    def __init__(self, operation_name: str, reraise: bool = False):
        self.operation_name = operation_name
        self.reraise = reraise
        self.exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception = exc_val
            logger.error(
                f"Error during {self.operation_name}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
            
            if self.reraise:
                return False
            
            return True  # Suppress exception
        
        return False

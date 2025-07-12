import logging
import time
from functools import wraps
from typing import Callable, Any
import uuid
from contextvars import copy_context

from src.core.logging_config import (
    setup_logging as setup_root_logging,
    request_id_var,
    user_id_var,
)


def setup_logging(name: str) -> logging.Logger:
    """Sets up logging for a given module/logger name.
    
    Args:
        name (str): The name of the module/logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure root logging is configured
    if not logging.getLogger().handlers:
        setup_root_logging()
    
    logger = logging.getLogger(name)
    logger.info(f"Logger initialized for module: {name}")
    return logger


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log the execution time of a function.
    
    Args:
        func (Callable): Function to wrap
        
    Returns:
        Callable: Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        try:
            logger.debug(f"Starting execution of {func.__name__}")
            result = func(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(
                f"Function {func.__name__} completed successfully",
                extra={
                    "performance_metric": True,
                    "function_name": func.__name__,
                    "duration_seconds": duration,
                    "status": "success"
                }
            )
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(
                f"Function {func.__name__} failed with error: {str(e)}",
                extra={
                    "performance_metric": True,
                    "function_name": func.__name__,
                    "duration_seconds": duration,
                    "status": "error",
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise
            
    return wrapper


def log_api_request(func: Callable) -> Callable:
    """Decorator for logging API requests with request ID tracking.
    
    Args:
        func (Callable): API endpoint function to wrap
        
    Returns:
        Callable: Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        logger = logging.getLogger(func.__module__)
        
        # Log request start
        logger.info(
            f"API Request started: {func.__name__}",
            extra={
                "api_endpoint": func.__name__,
                "request_id": request_id
            }
        )
        
        start_time = time.time()
        
        try:
            # Execute in context to preserve request_id
            ctx = copy_context()
            result = await ctx.run(func, *args, **kwargs)
            
            duration = time.time() - start_time
            
            logger.info(
                f"API Request completed: {func.__name__}",
                extra={
                    "api_endpoint": func.__name__,
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "status": "success",
                    "performance_metric": True
                }
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"API Request failed: {func.__name__}",
                extra={
                    "api_endpoint": func.__name__,
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "performance_metric": True
                },
                exc_info=True
            )
            raise
            
        finally:
            # Clear the request ID
            request_id_var.set(None)
            
    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        logger = logging.getLogger(func.__module__)
        
        # Log request start
        logger.info(
            f"API Request started: {func.__name__}",
            extra={
                "api_endpoint": func.__name__,
                "request_id": request_id
            }
        )
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            logger.info(
                f"API Request completed: {func.__name__}",
                extra={
                    "api_endpoint": func.__name__,
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "status": "success",
                    "performance_metric": True
                }
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"API Request failed: {func.__name__}",
                extra={
                    "api_endpoint": func.__name__,
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "status": "error",
                    "error_type": type(e).__name__,
                    "performance_metric": True
                },
                exc_info=True
            )
            raise
            
        finally:
            # Clear the request ID
            request_id_var.set(None)
            
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_database_operation(operation: str) -> Callable:
    """Decorator for logging database operations.
    
    Args:
        operation (str): Name of the database operation
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            start_time = time.time()
            
            logger.debug(f"Starting database operation: {operation}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Database operation completed: {operation}",
                    extra={
                        "db_operation": operation,
                        "duration_seconds": duration,
                        "status": "success",
                        "performance_metric": True
                    }
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Database operation failed: {operation}",
                    extra={
                        "db_operation": operation,
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "performance_metric": True
                    },
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


def log_security_event(event_type: str, user_id: str = None, details: dict = None):
    """Log a security-related event.
    
    Args:
        event_type (str): Type of security event
        user_id (str, optional): User ID associated with the event
        details (dict, optional): Additional details about the event
    """
    logger = logging.getLogger("security")
    
    logger.info(
        f"Security Event: {event_type}",
        extra={
            "security_event": True,
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {}
        }
    )

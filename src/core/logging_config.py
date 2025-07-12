import logging
import sys
from logging.handlers import RotatingFileHandler
import os
import json
from datetime import datetime
from contextvars import ContextVar
import traceback
from typing import Optional, Dict, Any

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured logs with context information."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Get context variables
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        
        # Build the base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }
        
        # Add context information if available
        if request_id:
            log_data["request_id"] = request_id
        if user_id:
            log_data["user_id"] = user_id
            
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        # Add any extra fields passed to the logger
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message',
                          'pathname', 'process', 'processName', 'relativeCreated', 'stack_info',
                          'thread', 'threadName', 'exc_info', 'exc_text']:
                log_data[key] = value
                
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Formatter for console output that's easier to read during development."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Get context variables
        request_id = request_id_var.get()
        
        # Color the level name
        levelname = record.levelname
        if sys.stdout.isatty():  # Only colorize if output is a terminal
            color = self.COLORS.get(levelname, self.RESET)
            levelname = f"{color}{levelname}{self.RESET}"
            
        # Build the log message
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Base format
        log_msg = f"{timestamp} | {levelname:8} | {record.name:30} | "
        
        # Add request ID if available
        if request_id:
            log_msg += f"[{request_id}] "
            
        # Add the actual message
        log_msg += record.getMessage()
        
        # Add location information for warnings and errors
        if record.levelno >= logging.WARNING:
            log_msg += f" | {record.filename}:{record.lineno} in {record.funcName}()"
            
        # Add exception information if present
        if record.exc_info:
            log_msg += "\n" + self.formatException(record.exc_info)
            
        return log_msg


def setup_logging(log_level=logging.INFO, log_dir="logs", environment="development"):
    """
    Configure comprehensive logging for the application.

    Args:
        log_level (int): Logging level (default: logging.INFO)
        log_dir (str): Directory to store log files
        environment (str): Environment name (development, production, etc.)
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers to prevent duplicate logs
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # Console Handler (for displaying logs in the terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use human-readable format for development, structured for production
    if environment == "development":
        console_formatter = HumanReadableFormatter()
    else:
        console_formatter = StructuredFormatter()
        
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Rotating) for general application logs - always structured
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "umbra_app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=5,  # Keep 5 backup files
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(file_handler)

    # Error File Handler (Rotating) for error-level logs
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "umbra_errors.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Performance logs handler
    perf_handler = RotatingFileHandler(
        os.path.join(log_dir, "umbra_performance.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(StructuredFormatter())
    perf_handler.addFilter(lambda record: hasattr(record, 'performance_metric'))
    root_logger.addHandler(perf_handler)
    
    # Security logs handler
    security_handler = RotatingFileHandler(
        os.path.join(log_dir, "umbra_security.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(StructuredFormatter())
    security_handler.addFilter(lambda record: hasattr(record, 'security_event'))
    root_logger.addHandler(security_handler)

    return root_logger


def log_performance_metrics(
    logger: logging.Logger, operation: str, start_time: float, end_time: float
):
    """
    Log performance metrics for an operation.

    Args:
        logger (logging.Logger): Logger instance
        operation (str): Name of the operation
        start_time (float): Start time of the operation
        end_time (float): End time of the operation
    """
    duration = end_time - start_time
    logger.info(f"Performance Metric: {operation} took {duration:.4f} seconds")


def log_database_connection(logger: logging.Logger, database_url: str):
    """
    Log database connection details securely.

    Args:
        logger (logging.Logger): Logger instance
        database_url (str): Database connection URL
    """
    # Mask sensitive information in the connection string for logging
    try:
        parts = database_url.split("@")
        if len(parts) > 1:
            masked_url = parts[0].split("//")[0] + "//***:***@" + parts[1]
        else:
            masked_url = database_url  # If no @, just log as is (might not contain sensitive info)
    except Exception:
        masked_url = "Error masking URL"  # Fallback in case of parsing error

    logger.info(f"Database Connection Attempted: {masked_url}")


# Example usage or a function to initialize logging from main app
def initialize_app_logging():
    """
    Initialize logging for the entire application.
    """
    logger = setup_logging()
    logger.info("Umbra Data Science Platform - Logging Initialized")
    return logger

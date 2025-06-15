import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging(log_level=logging.INFO, log_dir='logs'):
    """
    Configure comprehensive logging for the application.
    
    Args:
        log_level (int): Logging level (default: logging.INFO)
        log_dir (str): Directory to store log files
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
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Rotating) for general application logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'umbra_app.log'),
        maxBytes=10*1024*1024,  # 10 MB per file
        backupCount=5           # Keep 5 backup files
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error File Handler (Rotating) for error-level logs
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'umbra_errors.log'),
        maxBytes=10*1024*1024,
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter) # Use the same formatter as general file logs
    root_logger.addHandler(error_handler)

    return root_logger

def log_performance_metrics(logger: logging.Logger, operation: str, start_time: float, end_time: float):
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
        parts = database_url.split('@')
        if len(parts) > 1:
            masked_url = parts[0].split('//')[0] + '//***:***@' + parts[1]
        else:
            masked_url = database_url # If no @, just log as is (might not contain sensitive info)
    except Exception:
        masked_url = "Error masking URL" # Fallback in case of parsing error
        
    logger.info(f"Database Connection Attempted: {masked_url}")

# Example usage or a function to initialize logging from main app
def initialize_app_logging():
    """
    Initialize logging for the entire application.
    """
    logger = setup_logging()
    logger.info("Umbra Data Science Platform - Logging Initialized")
    return logger
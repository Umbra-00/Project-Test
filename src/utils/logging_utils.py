import logging

def setup_logging(name: str):
    """Sets up logging for a given module/logger name."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return logging.getLogger(name) 
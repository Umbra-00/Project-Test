# Copyright (c) 2024 Umbra. All rights reserved.
import os
import re
import logging

# Setup logging for the checker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def check_hardcoded_secrets():
    """Checks for hardcoded database password in Dockerfile."""
    dockerfile_path = os.path.join(PROJECT_ROOT, 'Dockerfile')
    if not os.path.exists(dockerfile_path):
        logger.warning(f"Dockerfile not found at {dockerfile_path}. Cannot check for hardcoded secrets.")
        return

    found_issue = False
    with open(dockerfile_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if "ENV DB_PASSWORD=" in line and "# IMPORTANT: Never hardcode sensitive passwords" not in line:
                logger.error(f"[SECURITY ALERT] Hardcoded DB_PASSWORD found in Dockerfile at line {line_num}. This is a critical security vulnerability for production deployments. Use Docker Secrets or environment variables for secure management.")
                found_issue = True
    if not found_issue:
        logger.info("No direct hardcoded DB_PASSWORD found in Dockerfile (or acknowledged as temporary).")

def check_dummy_data():
    """Checks for the presence of dummy course data in data_ingestion.py."""
    ingestion_file_path = os.path.join(PROJECT_ROOT, 'src', 'data_collection', 'data_ingestion.py')
    if not os.path.exists(ingestion_file_path):
        logger.warning(f"data_ingestion.py not found at {ingestion_file_path}. Cannot check for dummy data.")
        return

    with open(ingestion_file_path, 'r') as f:
        content = f.read()
        if "sample_courses = [" in content and "# For demonstration, let's ingest a few dummy courses" in content:
            logger.warning("[PRODUCTION READINESS] Dummy course data detected in `src/data_collection/data_ingestion.py`. This should be replaced with actual data sources for production.")

def check_temporary_files():
    """Checks for known temporary development files."""
    temporary_files = [
        os.path.join(PROJECT_ROOT, 'test_env.py'),
    ]
    for temp_file in temporary_files:
        if os.path.exists(temp_file):
            logger.warning(f"[CLEANUP] Temporary file detected: {temp_file}. Consider removing for production deployment.")

def check_debug_prints():
    """Checks for the presence of explicit debug logging in key files."""
    db_utils_file_path = os.path.join(PROJECT_ROOT, 'src', 'data_engineering', 'db_utils.py')
    
    if not os.path.exists(db_utils_file_path):
        logger.warning(f"db_utils.py not found at {db_utils_file_path}. Cannot check for debug prints.")
        return

    with open(db_utils_file_path, 'r') as f:
        content = f.read()
        # Look for the specific DEBUG prints we added
        if "DEBUG: DB_USER:" in content or \
           "DEBUG: DB_PASSWORD (from .env):" in content or \
           "DEBUG: Constructed DATABASE_URL:" in content:
            logger.info("[DEBUGGING] Explicit DEBUG prints found in `src/data_engineering/db_utils.py`. These are useful for development but should be made conditional or removed for production to reduce log verbosity and potential information leakage.")

def run_production_readiness_checks():
    """Runs all defined production readiness checks."""
    logger.info("\n--- Running Production Readiness Checks ---")
    check_hardcoded_secrets()
    check_dummy_data()
    check_temporary_files()
    check_debug_prints()
    logger.info("--- Production Readiness Checks Complete ---")

if __name__ == "__main__":
    run_production_readiness_checks() 
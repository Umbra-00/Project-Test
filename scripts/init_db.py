#!/usr/bin/env python3
"""
Database initialization script for Umbra Educational Data Platform.
This script creates the database tables and runs initial migrations.
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sqlalchemy import create_engine, text
from src.core.database import Base
from src.data_engineering.database_models import Course, User
from src.core.logging_config import setup_logging

logger = setup_logging()

def init_database():
    """Initialize the database by creating tables."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        logger.info("Connecting to database...")
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("SELECT to_regclass('public.courses')"))
            courses_table_exists = result.scalar() is not None
            
            result = conn.execute(text("SELECT to_regclass('public.users')"))
            users_table_exists = result.scalar() is not None
            
            if courses_table_exists and users_table_exists:
                logger.info("Database tables created successfully")
                return True
            else:
                logger.error("Failed to create some tables")
                return False
                
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def wait_for_database():
    """Wait for database to be ready."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database is ready")
                return True
        except Exception as e:
            logger.info(f"Database not ready: {e}, attempt {retry_count + 1}/{max_retries}")
            retry_count += 1
            time.sleep(2)
    
    logger.error("Database connection timed out")
    return False

def main():
    """Main function to initialize the database."""
    logger.info("Starting database initialization...")
    
    if not wait_for_database():
        logger.error("Database is not ready")
        sys.exit(1)
    
    if not init_database():
        logger.error("Database initialization failed")
        sys.exit(1)
    
    logger.info("Database initialization completed successfully")

if __name__ == "__main__":
    main()

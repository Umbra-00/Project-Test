# Copyright (c) 2024 Umbra. All rights reserved.
# src/data_engineering/db_utils.py
# Provides utility functions for robust database connection, session management,
# connection pooling, error handling, and logging.

import os
import time
from functools import wraps
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

from src.utils.logging_utils import setup_logging # Import the new logging utility

# Load environment variables from .env file
# Corrected path for .env at project root
load_dotenv(dotenv_path=os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'config', '.env'))

# Setup logging
logger = setup_logging(__name__) # Use the reusable setup_logging function

# --- Configuration ---
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'learning_platform_db')
DB_USER = os.getenv('DB_USER', 'learning_user')
DB_PASSWORD = os.getenv('DB_PASSWORD') # This will come from the .env file

# Consider a more robust secret management solution for production
# For portfolio, ensure .env is not committed and permissions are strict (e.g., 600)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Temporary debug prints ---
# logger.info(f"DEBUG: DB_USER: {DB_USER}")
# logger.info(f"DEBUG: DB_PASSWORD (from .env): {DB_PASSWORD}")
# logger.info(f"DEBUG: Constructed DATABASE_URL: {DATABASE_URL}")
# --- End temporary debug prints ---

# --- Connection Pooling ---
# Configure engine with connection pooling
# pool_size: The number of connections to keep open in the pool.
# max_overflow: The number of connections that can be opened beyond the pool_size.
# pool_recycle: Recycles connections after this many seconds. Prevents stale connections.
# pool_timeout: Maximum wait time for a connection from the pool.
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600, # Recycle connections every hour
    pool_timeout=30,
    echo=False # Set to True for verbose SQLAlchemy logging (useful for debugging)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Error Handling & Retry Logic with Exponential Backoff ---
def retry_db_operation(max_tries=5, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Attempt {i+1}/{max_tries} failed for {func.__name__}: {e}")
                    if i < max_tries - 1:
                        delay = base_delay * (2 ** i) # Exponential backoff
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.critical(f"All {max_tries} attempts failed for {func.__name__}. Giving up.")
                        raise # Re-raise the last exception
        return wrapper
    return decorator

# --- Database Health Check ---
@retry_db_operation(max_tries=3)
def check_db_health():
    """Checks the database connection health."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        logger.info("Database health check: Connection successful.")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# --- Dependency for getting a database session (for FastAPI/API context) ---
def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SQL Injection Prevention Note ---
# SQLAlchemy ORM and its Core Expression Language are designed to prevent SQL injection
# by sanitizing inputs automatically. Avoid using f-strings or direct string formatting
# for query parameters with user input. Always use parameter binding or ORM methods.
# Example of safe query: session.query(User).filter(User.username == user_input).first()
# Example of unsafe query (DO NOT USE WITH USER INPUT): session.execute(f"SELECT * FROM users WHERE username = '{user_input}'")
# For raw SQL, always use text() with .bindparams():
# session.execute(text("SELECT * FROM users WHERE username = :username").bindparams(username=user_input))

if __name__ == "__main__":
    print("--- Database Utilities Module ---")
    print("Attempting database health check...")
    if check_db_health():
        print("Database is healthy!")
        # Example of using a session
        try:
            with SessionLocal() as session:
                # You can add a simple query here to test session if tables exist
                # from database_models import User
                # users = session.query(User).limit(1).all()
                # print(f"Found {len(users)} users (if any).")
                pass
        except Exception as e:
            logger.error(f"Error during session test: {e}")
    else:
        print("Database is not healthy. Check logs for details.")

    print("\nRemember to configure your `config/.env` file with correct DB credentials.")
    print("Ensure .env file has secure permissions (e.g., 600) and is NOT committed to Git.") 
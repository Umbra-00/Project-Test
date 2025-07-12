# Copyright (c) 2024 Umbra. All rights reserved.
# src/data_engineering/db_utils.py
# Provides utility functions for robust database connection, session management,
# connection pooling, error handling, and logging.

import time
from functools import wraps
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from src.core.config import settings  # Import settings
from src.utils.logging_utils import setup_logging  # Import the new logging utility

# from urllib.parse import quote_plus # This is no longer needed

# Setup logging
logger = setup_logging(__name__)

# --- Configuration ---
# The DATABASE_URL is now expected to be the full connection string directly.
DATABASE_URL = settings.DATABASE_URL  # Use settings.DATABASE_URL


# --- Temporary debug prints ---
logger.info(f"DEBUG: Constructed DATABASE_URL: {DATABASE_URL}")
# --- End temporary debug prints ---

# Configure engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections every hour
    pool_timeout=30,
    echo=False,  # Set to True for verbose SQLAlchemy logging (useful for debugging)
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
                    logger.error(
                        f"Attempt {i+1}/{max_tries} failed for {func.__name__}: {e}"
                    )
                    if i < max_tries - 1:
                        delay = base_delay * (2**i)  # Exponential backoff
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.critical(
                            f"All {max_tries} attempts failed for {func.__name__}. Giving up."
                        )
                        raise  # Re-raise the last exception

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
# For raw SQL, always use text() with .bindparams():
# session.execute(text("SELECT * FROM users WHERE username = :username").bindparams(username=user_input))


# --- Database Schema Management ---
def create_all_tables():
    """Creates all tables defined in Base metadata."""
    logger.info("Attempting to create all database tables...")
    try:
        # Import Base and engine from current module
        from src.data_engineering.database_models import Base

        Base.metadata.create_all(engine)
        logger.info("All database tables created successfully.")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False


def drop_all_tables():
    """Drops all tables defined in Base metadata."""
    logger.info("Attempting to drop all database tables...")
    try:
        from src.data_engineering.database_models import Base

        Base.metadata.drop_all(engine)
        logger.info("All database tables dropped successfully.")
        return True
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        return False


if __name__ == "__main__":
    print("--- Database Utilities Module ---")
    print("Attempting database health check...")
    if check_db_health():
        print("Database is healthy!")

        # Add a prompt to the user before dropping/creating tables
        response = input(
            "Do you want to (d)rop and (c)reate all tables, or (s)kip? (d/c/s): "
        ).lower()
        if response == "d":
            if drop_all_tables():
                print("Tables dropped.")
            else:
                print("Failed to drop tables.")

        if response == "c":
            if create_all_tables():
                print("Tables created.")
            else:
                print("Failed to create tables.")
        elif response == "dc":
            if drop_all_tables():
                print("Tables dropped.")
                if create_all_tables():
                    print("Tables created.")
                else:
                    print("Failed to create tables.")
            else:
                print("Failed to drop tables.")

        # --- Initial Admin User Creation Logic ---
        # Removed for simplified deployment

    else:
        print("Database is not healthy. Check logs for details.")

    print(
        "\nRemember to configure your `.env` file with correct DB credentials and initial admin user details."
    )
    print(
        "Ensure .env file has secure permissions (e.g., 600) and is NOT committed to Git."
    )

    # Database Connection Credentials:
    # DB_HOST is set to 'localhost' for local Python script execution (e.g., db_utils.py directly).
    # Docker Compose will override this to 'db' for services running inside containers (e.g., your FastAPI app).
    # DB_PORT=5432
    # DB_NAME=learning_platform_db
    # DB_USER=your_desired_db_user      # <-- **IMPORTANT: REPLACE THIS** with a strong username for PostgreSQL
    # DB_PASSWORD=your_very_strong_db_password # <-- **IMPORTANT: REPLACE THIS** with a strong password for PostgreSQL

    # Initial Application Admin User Credentials:
    # These will be used by our setup script to securely create the first admin user in your database.
    # IMPORTANT: Choose a strong, unique username and password for this administrative user.
    # INITIAL_ADMIN_USERNAME=your_desired_admin_username
    # INITIAL_ADMIN_PASSWORD=strong_admin_password

    # Add any other backend-specific environment variables here as needed for your project:
    # Example: If you plan to use MLflow for tracking:
    # MLFLOW_TRACKING_URI=http://mlflow:5000

    # Example: For securing your FastAPI application with JWT tokens, you'll need a secret key:
    # SECRET_KEY=a_very_long_and_random_string_for_security

    # Example: If you integrate with external APIs, you might put their keys here:
    # API_KEY_EXTERNAL_SERVICE=your_external_api_key_here

    # These lines below are comments/instructions for the .env file and should NOT be in the python script.
    # They are being removed to fix the NameError.
    # DB_PORT=5432
    # DB_NAME=learning_platform_db
    # DB_USER=your_desired_db_user      # <-- **IMPORTANT: REPLACE THIS** with a strong username for PostgreSQL
    # DB_PASSWORD=your_very_strong_db_password # <-- **IMPORTANT: REPLACE THIS** with a strong password for PostgreSQL

    # INITIAL_ADMIN_USERNAME=your_desired_admin_username
    # INITIAL_ADMIN_PASSWORD=strong_admin_password

    # MLFLOW_TRACKING_URI=http://mlflow:5000
    # SECRET_KEY=a_very_long_and_random_string_for_security
    # API_KEY_EXTERNAL_SERVICE=your_external_api_key_here

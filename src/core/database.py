from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import DisconnectionError
import time
import logging

from src.core.config import settings

# Setup logger
logger = logging.getLogger(__name__)

# Use DATABASE_URL from settings, which will be populated by environment variables
DATABASE_URL = settings.DATABASE_URL

# Log database connection attempt
logger.info(
    "Initializing database connection",
    extra={
        "database_host": settings.DB_HOST,
        "database_name": settings.DB_NAME,
        "database_user": settings.DB_USER,
        "environment": settings.ENVIRONMENT,
    },
)

# Create SQLAlchemy engine with connection pooling and error handling
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for better error tracking
        pool_pre_ping=True,  # Test connections before using them
        echo=(settings.ENVIRONMENT == "development"),  # SQL logging in development
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 second statement timeout
        },
    )

    # Add event listeners for logging
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.info(
            "Database connection established", extra={"performance_metric": True}
        )

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("Database connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        logger.debug("Database connection returned to pool")

except Exception as e:
    logger.error(
        f"Failed to create database engine: {str(e)}",
        extra={"error_type": type(e).__name__},
        exc_info=True,
    )
    raise

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency that creates a new database session for each request.
    Ensures proper session management and connection handling.
    """
    start_time = time.time()
    db = SessionLocal()

    try:
        logger.debug("Database session created")
        yield db

        # Log successful session completion
        duration = time.time() - start_time
        logger.debug(
            f"Database session completed successfully",
            extra={"performance_metric": True, "duration_seconds": duration},
        )

    except Exception as e:
        # Log session errors
        duration = time.time() - start_time
        logger.error(
            f"Database session error: {str(e)}",
            extra={
                "performance_metric": True,
                "duration_seconds": duration,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise

    finally:
        db.close()
        logger.debug("Database session closed")


def test_database_connection():
    """
    Test database connectivity.
    Returns True if connection is successful, False otherwise.
    """
    start_time = time.time()
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
            duration = time.time() - start_time
            logger.info(
                "Database connection test successful",
                extra={
                    "performance_metric": True,
                    "db_operation": "test_connection",
                    "duration_seconds": duration,
                },
            )
            return True
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Database connection test failed: {str(e)}",
            extra={
                "error_type": type(e).__name__,
                "performance_metric": True,
                "db_operation": "test_connection",
                "duration_seconds": duration,
            },
            exc_info=True,
        )
        return False

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from src.core.config import settings # Import settings

# Use DATABASE_URL from settings, which will be populated by environment variables
DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine with connection pooling and error handling
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for better error tracking
    pool_pre_ping=True,  # Test connections before using them
    echo=False,  # Set to True for SQL logging during development
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency that creates a new database session for each request.
    Ensures proper session management and connection handling.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "umbra_user"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "umbra_db"

    # Security Settings
    SECRET_KEY: str = "default-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Deployment Environment
    ENVIRONMENT: str = "development"

    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # Admin Credentials
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "admin"

    # FastAPI Settings
    FASTAPI_BASE_URL: str = "http://localhost:8000/api/v1"

    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env that are not defined here
        case_sensitive = False

    def __init__(self, **values):
        super().__init__(**values)
        # Build DATABASE_URL if not explicitly provided
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )


# Create settings instance
settings = Settings()

# Log configuration on startup
logger = logging.getLogger(__name__)
logger.info(
    f"Application configured for {settings.ENVIRONMENT} environment",
    extra={
        "environment": settings.ENVIRONMENT,
        "database_host": settings.DB_HOST,
        "database_name": settings.DB_NAME,
        "log_level": settings.LOG_LEVEL
    }
)

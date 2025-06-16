from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str # Render will provide this

    # Security Settings
    SECRET_KEY: str # Render will provide this
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Deployment Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env that are not defined here


settings = Settings()

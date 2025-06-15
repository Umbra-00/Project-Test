from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    # Database Configuration
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'umbra_user'
    DB_PASSWORD: str = secrets.token_urlsafe(16)
    DB_NAME: str = 'umbra_db'

    # Sqlalchemy Database URL
    @property
    def DATABASE_URL(self) -> str:
        # This will be overridden by environment variables in deployment
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Security Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Deployment Environment
    ENVIRONMENT: str = 'development'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore' # Ignore extra fields in .env that are not defined here

settings = Settings() 
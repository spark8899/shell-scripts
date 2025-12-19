# app/config.py
import os
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env file from the parent directory
# This makes it work regardless of where the script is run from
env_path = Path('.') / '../.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    # Database settings
    DATABASE_URL: str
    DEFAULT_ADMIN_USER: str
    DEFAULT_ADMIN_PASSWORD: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging settings
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT: int = 5

    # Zookeeper settings
    ZOOKEEPER_HOSTS: str = "127.0.0.1:2181"

    class Config:
        # If using older pydantic-settings or just pydantic:
        # env_file = "../.env"
        # env_file_encoding = 'utf-8'
        # case_sensitive = True # Usually defaults are fine

        # For pydantic-settings v2+
        #env_file = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True)
        pass # Loading is handled manually above for robustness

# Create a single instance of settings to be imported elsewhere
settings = Settings()

# Ensure the log directory exists
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(parents=True, exist_ok=True)

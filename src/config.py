import yaml
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class APISettings:
    """Loads API endpoints and parameters from settings.yml"""
    def __init__(self, path="settings.yml"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found at: {path}")
        with open(path, "r") as f:
            self._config = yaml.safe_load(f)

    @property
    def news_api(self):
        return self._config.get("news_api", {})

    @property
    def market_data(self):
        return self._config.get("market_data", {})

class Settings(BaseSettings):
    """Loads environment variables and API settings."""
    # From .env file
    news_api_key: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    db_name: str
    db_name_staging: str = "stockometry_staging"  # Default staging database name

    # From settings.yml
    api: APISettings = APISettings()

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the Settings."""
    return Settings()

# Make settings easily accessible
settings = get_settings()

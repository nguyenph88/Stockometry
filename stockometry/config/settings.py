"""
Stockometry Configuration Management
Consolidated configuration loading from settings.yml file.
"""

import yaml
from functools import lru_cache
import os
from typing import Dict, Any

class Settings:
    """Consolidated configuration for Stockometry application."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Look for settings.yml in the same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "settings.yml")
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
        with open(config_path, "r") as f:
            self._config = yaml.safe_load(f)
    
    # --- Environment Configuration ---
    @property
    def environment(self) -> str:
        return self._config.get("environment", "development")
    
    @property
    def log_level(self) -> str:
        return self._config.get("log_level", "INFO")
    
    # --- API Configuration ---
    @property
    def news_api_key(self) -> str:
        return self._config.get("apis", {}).get("news_api_key", "")
    
    @property
    def news_api(self) -> Dict[str, Any]:
        return self._config.get("apis", {}).get("news_api", {})
    
    # --- Database Configuration ---
    @property
    def db_host(self) -> str:
        return self._config.get("database", {}).get("host", "localhost")
    
    @property
    def db_port(self) -> str:
        return self._config.get("database", {}).get("port", "5432")
    
    @property
    def db_name(self) -> str:
        return self._config.get("database", {}).get("name", "stockometry")
    
    @property
    def db_user(self) -> str:
        return self._config.get("database", {}).get("user", "postgres")
    
    @property
    def db_password(self) -> str:
        return self._config.get("database", {}).get("password", "")
    
    @property
    def db_name_staging(self) -> str:
        return self._config.get("database", {}).get("name_staging", "stockometry_staging")
    
    @property
    def db_name_active(self) -> str:
        """Returns the active database name based on environment setting."""
        if self.environment == "staging":
            return self.db_name_staging
        else:
            return self.db_name
    
    # --- Market Data Configuration ---
    @property
    def market_data(self) -> Dict[str, Any]:
        return self._config.get("market_data", {})
    
    # --- Scheduler Configuration ---
    @property
    def scheduler_timezone(self) -> str:
        return self._config.get("scheduler", {}).get("timezone", "UTC")
    
    @property
    def scheduler_news_interval_hours(self) -> int:
        return self._config.get("scheduler", {}).get("news_interval_hours", 1)
    
    @property
    def scheduler_market_data_hour(self) -> int:
        return self._config.get("scheduler", {}).get("market_data_hour", 1)
    
    @property
    def scheduler_nlp_interval_minutes(self) -> int:
        return self._config.get("scheduler", {}).get("nlp_interval_minutes", 15)
    
    @property
    def scheduler_final_report_hour(self) -> int:
        return self._config.get("scheduler", {}).get("final_report_hour", 2)
    
    @property
    def scheduler_final_report_minute(self) -> int:
        return self._config.get("scheduler", {}).get("final_report_minute", 30)
    
    # --- NLP Configuration ---
    @property
    def nlp_spacy_model(self) -> str:
        return self._config.get("nlp", {}).get("spacy_model", "en_core_web_sm")
    
    @property
    def nlp_finbert_model(self) -> str:
        return self._config.get("nlp", {}).get("finbert_model", "ProsusAI/finbert")
    
    @property
    def nlp_confidence_threshold(self) -> float:
        return self._config.get("nlp", {}).get("confidence_threshold", 0.3)
    
    # --- Analysis Configuration ---
    @property
    def analysis_historical_days(self) -> int:
        return self._config.get("analysis", {}).get("historical_days", 6)
    
    @property
    def analysis_sector_thresholds(self) -> Dict[str, Any]:
        return self._config.get("analysis", {}).get("sector_thresholds", {})
    
    @property
    def analysis_extreme_sentiment_threshold(self) -> float:
        return self._config.get("analysis", {}).get("extreme_sentiment_threshold", 0.9)
    
    # --- Output Configuration ---
    @property
    def output_json_directory(self) -> str:
        return self._config.get("output", {}).get("json_directory", "exports")
    
    @property
    def output_filename_format(self) -> str:
        return self._config.get("output", {}).get("filename_format", "report_YYYY-MM-DD_HHMMSS_{run_source}.json")

@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the Settings."""
    return Settings()

# Make settings easily accessible
settings = get_settings()

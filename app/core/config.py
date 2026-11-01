"""
Application configuration management using Pydantic settings.
Loads configuration from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    """
    
    # Application
    APP_NAME: str = "FaultScope"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # ML Configuration
    MIN_TRAINING_SAMPLES: int = 100
    MODEL_PATH: str = "models/"
    
    # Rule-Based Detector Thresholds
    RULE_CPU_THRESHOLD: float = 80.0
    RULE_MEMORY_THRESHOLD: float = 85.0
    RULE_ERROR_RATE_THRESHOLD: float = 10.0
    RULE_LATENCY_THRESHOLD: float = 2000.0  # milliseconds
    
    # Isolation Forest Configuration
    ISOLATION_FOREST_CONTAMINATION: float = 0.1
    ISOLATION_FOREST_N_ESTIMATORS: int = 100
    ISOLATION_FOREST_RANDOM_STATE: int = 42
    
    # Incident Severity Thresholds
    SEVERITY_CRITICAL_SCORE: float = 0.9
    SEVERITY_HIGH_SCORE: float = 0.75
    SEVERITY_MEDIUM_SCORE: float = 0.5
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are loaded only once and reused.
    This is important for performance and consistency.
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()

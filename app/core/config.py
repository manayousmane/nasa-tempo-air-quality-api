"""
Core application configuration using Pydantic Settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/nasa_tempo"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # NASA Earth Data
    NASA_EARTHDATA_USERNAME: Optional[str] = None
    NASA_EARTHDATA_PASSWORD: Optional[str] = None
    NASA_EARTHDATA_TOKEN: Optional[str] = None
    TEMPO_DATA_URL: str = "https://earthdata.nasa.gov/api/tempo"
    
    # Weather APIs
    OPENWEATHER_API_KEY: Optional[str] = None
    NOAA_API_TOKEN: Optional[str] = None
    
    # Air Quality Data Sources
    EPA_API_KEY: Optional[str] = None
    OPENAQ_API_KEY: Optional[str] = None
    PANDORA_API_URL: str = "https://data.pandonia-global-network.org/api"
    
    # Premium Air Quality APIs
    PURPLEAIR_API_KEY: Optional[str] = None
    AIRVISUAL_API_KEY: Optional[str] = None
    BREEZOMETER_API_KEY: Optional[str] = None
    AQICN_API_TOKEN: str = "demo"
    
    # ML Model Configuration
    MODEL_UPDATE_INTERVAL: int = 3600  # seconds
    PREDICTION_HORIZON: int = 24  # hours
    MODEL_DATA_PATH: str = "./models/trained/"
    
    # Alert System
    ALERT_CHECK_INTERVAL: int = 300  # seconds
    EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Monitoring
    PROMETHEUS_PORT: int = 8001
    HEALTH_CHECK_INTERVAL: int = 60
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
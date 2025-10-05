"""
Database models for air quality data.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Location(Base):
    """Geographic location model."""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    country = Column(String(100), nullable=False)
    state = Column(String(100))
    city = Column(String(100))
    postal_code = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    air_quality_measurements = relationship("AirQualityMeasurement", back_populates="location")
    weather_data = relationship("WeatherData", back_populates="location")
    predictions = relationship("AirQualityPrediction", back_populates="location")


class AirQualityMeasurement(Base):
    """Air quality measurement data from various sources."""
    __tablename__ = "air_quality_measurements"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    source = Column(String(50), nullable=False)  # TEMPO, EPA, OpenAQ, etc.
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Air quality parameters
    pm25 = Column(Float)  # PM2.5 concentration (μg/m³)
    pm10 = Column(Float)  # PM10 concentration (μg/m³)
    no2 = Column(Float)   # Nitrogen dioxide (ppb)
    o3 = Column(Float)    # Ozone (ppb)
    co = Column(Float)    # Carbon monoxide (ppm)
    so2 = Column(Float)   # Sulfur dioxide (ppb)
    hcho = Column(Float)  # Formaldehyde (ppb)
    
    # Air Quality Index
    aqi = Column(Integer)
    aqi_category = Column(String(50))  # Good, Moderate, Unhealthy, etc.
    
    # Data quality indicators
    quality_flag = Column(String(20))  # good, suspect, bad
    confidence = Column(Float)  # 0.0 to 1.0
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location = relationship("Location", back_populates="air_quality_measurements")


class WeatherData(Base):
    """Weather data for air quality correlation."""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(50), nullable=False)  # OpenWeather, NOAA, etc.
    
    # Weather parameters
    temperature = Column(Float)  # Celsius
    humidity = Column(Float)     # Percentage
    pressure = Column(Float)     # hPa
    wind_speed = Column(Float)   # m/s
    wind_direction = Column(Float)  # degrees
    precipitation = Column(Float)   # mm
    cloud_cover = Column(Float)     # percentage
    visibility = Column(Float)      # km
    uv_index = Column(Float)
    
    # Weather conditions
    condition = Column(String(100))  # Clear, Cloudy, Rain, etc.
    description = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location = relationship("Location", back_populates="weather_data")


class AirQualityPrediction(Base):
    """Air quality predictions from ML models."""
    __tablename__ = "air_quality_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    model_version = Column(String(50), nullable=False)
    prediction_timestamp = Column(DateTime(timezone=True), nullable=False)
    forecast_timestamp = Column(DateTime(timezone=True), nullable=False)
    forecast_horizon = Column(Integer, nullable=False)  # hours ahead
    
    # Predicted values
    predicted_pm25 = Column(Float)
    predicted_pm10 = Column(Float)
    predicted_no2 = Column(Float)
    predicted_o3 = Column(Float)
    predicted_aqi = Column(Integer)
    predicted_category = Column(String(50))
    
    # Confidence intervals
    pm25_confidence_low = Column(Float)
    pm25_confidence_high = Column(Float)
    aqi_confidence_low = Column(Integer)
    aqi_confidence_high = Column(Integer)
    
    # Model metadata
    model_confidence = Column(Float)  # 0.0 to 1.0
    feature_importance = Column(Text)  # JSON string
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    location = relationship("Location", back_populates="predictions")


class Alert(Base):
    """Air quality alerts and notifications."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # health, visibility, etc.
    severity = Column(String(20), nullable=False)    # low, moderate, high, very_high
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert timing
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Alert triggers
    triggered_by = Column(String(100))  # AQI threshold, PM2.5 level, etc.
    threshold_value = Column(Float)
    actual_value = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DataSource(Base):
    """Configuration for different data sources."""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # satellite, ground, weather
    api_endpoint = Column(String(500))
    is_active = Column(Boolean, default=True)
    update_frequency = Column(Integer)  # minutes
    last_update = Column(DateTime(timezone=True))
    
    # API configuration
    requires_auth = Column(Boolean, default=False)
    auth_type = Column(String(50))  # api_key, oauth, basic
    rate_limit = Column(Integer)    # requests per hour
    
    # Data quality
    reliability_score = Column(Float)  # 0.0 to 1.0
    coverage_area = Column(Text)       # JSON string describing coverage
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
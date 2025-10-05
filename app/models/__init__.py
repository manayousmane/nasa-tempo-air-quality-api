"""
Models package initialization.
"""
from .database import Base, Location, AirQualityMeasurement, WeatherData, AirQualityPrediction, Alert, DataSource
from .schemas import (
    LocationCreate, Location as LocationSchema,
    AirQualityMeasurementCreate, AirQualityMeasurement as AirQualityMeasurementSchema,
    WeatherDataCreate, WeatherData as WeatherDataSchema,
    AirQualityPredictionCreate, AirQualityPrediction as AirQualityPredictionSchema,
    AlertCreate, Alert as AlertSchema,
    AirQualityResponse, ForecastResponse, HistoricalResponse,
    AirQualityQuery, AQICategory, AlertSeverity, DataSource as DataSourceEnum
)

__all__ = [
    # Database models
    "Base", "Location", "AirQualityMeasurement", "WeatherData", 
    "AirQualityPrediction", "Alert", "DataSource",
    
    # Pydantic schemas
    "LocationCreate", "LocationSchema",
    "AirQualityMeasurementCreate", "AirQualityMeasurementSchema",
    "WeatherDataCreate", "WeatherDataSchema",
    "AirQualityPredictionCreate", "AirQualityPredictionSchema",
    "AlertCreate", "AlertSchema",
    "AirQualityResponse", "ForecastResponse", "HistoricalResponse",
    "AirQualityQuery", "AQICategory", "AlertSeverity", "DataSourceEnum"
]
"""
Pydantic models for API request/response schemas.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class AQICategory(str, Enum):
    """Air Quality Index categories."""
    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DataSource(str, Enum):
    """Available data sources."""
    TEMPO = "TEMPO"
    NASA_TEMPO = "NASA_TEMPO"
    EPA = "EPA"
    OPENAQ = "OpenAQ"
    PANDORA = "Pandora"
    OPENWEATHER = "OpenWeather"
    NOAA = "NOAA"
    NASA_SATELLITE_MODEL = "NASA_Satellite_Model"


# Base schemas
class LocationBase(BaseModel):
    """Base location schema - MISE À JOUR avec support États/Provinces."""
    name: str = Field(..., description="Location name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    country: str = Field(..., description="Country name")
    state_province: Optional[str] = Field(None, description="State/Province name")
    state_province_code: Optional[str] = Field(None, description="State/Province code")
    city: Optional[str] = Field(None, description="City name")
    region: Optional[str] = Field(None, description="Geographic region")
    timezone: Optional[str] = Field(None, description="Timezone")
    postal_code: Optional[str] = Field(None, description="Postal code")


class LocationCreate(LocationBase):
    """Schema for creating a new location."""
    pass


class Location(LocationBase):
    """Complete location schema."""
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Air Quality schemas
class AirQualityMeasurementBase(BaseModel):
    """Base air quality measurement schema."""
    source: DataSource = Field(..., description="Data source")
    timestamp: datetime = Field(..., description="Measurement timestamp")
    
    # Air quality parameters
    pm25: Optional[float] = Field(None, ge=0, description="PM2.5 concentration (μg/m³)")
    pm10: Optional[float] = Field(None, ge=0, description="PM10 concentration (μg/m³)")
    no2: Optional[float] = Field(None, ge=0, description="NO2 concentration (ppb)")
    o3: Optional[float] = Field(None, ge=0, description="O3 concentration (ppb)")
    co: Optional[float] = Field(None, ge=0, description="CO concentration (ppm)")
    so2: Optional[float] = Field(None, ge=0, description="SO2 concentration (ppb)")
    hcho: Optional[float] = Field(None, ge=0, description="HCHO concentration (ppb)")
    
    # Air Quality Index
    aqi: Optional[int] = Field(None, ge=0, le=500, description="Air Quality Index")
    aqi_category: Optional[AQICategory] = Field(None, description="AQI category")
    
    # Data quality
    quality_flag: Optional[str] = Field("good", description="Data quality flag")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Measurement confidence")


class AirQualityMeasurementCreate(AirQualityMeasurementBase):
    """Schema for creating air quality measurements."""
    location_id: int = Field(..., description="Location ID")


class AirQualityMeasurement(AirQualityMeasurementBase):
    """Complete air quality measurement schema."""
    id: int
    location_id: int
    created_at: datetime
    location: Optional[Location] = None

    class Config:
        from_attributes = True


# Weather schemas
class WeatherDataBase(BaseModel):
    """Base weather data schema."""
    timestamp: datetime = Field(..., description="Weather data timestamp")
    source: DataSource = Field(..., description="Weather data source")
    
    # Weather parameters
    temperature: Optional[float] = Field(None, description="Temperature (°C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity (%)")
    pressure: Optional[float] = Field(None, ge=0, description="Pressure (hPa)")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed (m/s)")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Wind direction (degrees)")
    precipitation: Optional[float] = Field(None, ge=0, description="Precipitation (mm)")
    cloud_cover: Optional[float] = Field(None, ge=0, le=100, description="Cloud cover (%)")
    visibility: Optional[float] = Field(None, ge=0, description="Visibility (km)")
    uv_index: Optional[float] = Field(None, ge=0, description="UV index")
    
    # Weather conditions
    condition: Optional[str] = Field(None, description="Weather condition")
    description: Optional[str] = Field(None, description="Weather description")


class WeatherDataCreate(WeatherDataBase):
    """Schema for creating weather data."""
    location_id: int = Field(..., description="Location ID")


class WeatherData(WeatherDataBase):
    """Complete weather data schema."""
    id: int
    location_id: int
    created_at: datetime
    location: Optional[Location] = None

    class Config:
        from_attributes = True


# Prediction schemas
class AirQualityPredictionBase(BaseModel):
    """Base air quality prediction schema."""
    model_version: str = Field(..., description="ML model version")
    prediction_timestamp: datetime = Field(..., description="When prediction was made")
    forecast_timestamp: datetime = Field(..., description="Forecast target time")
    forecast_horizon: int = Field(..., ge=1, le=168, description="Hours ahead")
    
    # Predicted values
    predicted_pm25: Optional[float] = Field(None, ge=0, description="Predicted PM2.5")
    predicted_pm10: Optional[float] = Field(None, ge=0, description="Predicted PM10")
    predicted_no2: Optional[float] = Field(None, ge=0, description="Predicted NO2")
    predicted_o3: Optional[float] = Field(None, ge=0, description="Predicted O3")
    predicted_aqi: Optional[int] = Field(None, ge=0, le=500, description="Predicted AQI")
    predicted_category: Optional[AQICategory] = Field(None, description="Predicted AQI category")
    
    # Confidence intervals
    pm25_confidence_low: Optional[float] = Field(None, description="PM2.5 lower confidence")
    pm25_confidence_high: Optional[float] = Field(None, description="PM2.5 upper confidence")
    aqi_confidence_low: Optional[int] = Field(None, description="AQI lower confidence")
    aqi_confidence_high: Optional[int] = Field(None, description="AQI upper confidence")
    
    # Model metadata
    model_confidence: Optional[float] = Field(None, ge=0, le=1, description="Model confidence")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Feature importance")


class AirQualityPredictionCreate(AirQualityPredictionBase):
    """Schema for creating predictions."""
    location_id: int = Field(..., description="Location ID")


class AirQualityPrediction(AirQualityPredictionBase):
    """Complete prediction schema."""
    id: int
    location_id: int
    created_at: datetime
    location: Optional[Location] = None

    class Config:
        from_attributes = True


# Alert schemas
class AlertBase(BaseModel):
    """Base alert schema."""
    alert_type: str = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., max_length=255, description="Alert title")
    message: str = Field(..., description="Alert message")
    start_time: datetime = Field(..., description="Alert start time")
    end_time: Optional[datetime] = Field(None, description="Alert end time")
    triggered_by: Optional[str] = Field(None, description="What triggered the alert")
    threshold_value: Optional[float] = Field(None, description="Threshold value")
    actual_value: Optional[float] = Field(None, description="Actual value")


class AlertCreate(AlertBase):
    """Schema for creating alerts."""
    location_id: int = Field(..., description="Location ID")


class Alert(AlertBase):
    """Complete alert schema."""
    id: int
    location_id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# API Response schemas
class AirQualityResponse(BaseModel):
    """Air quality API response."""
    location: Location
    current_measurement: Optional[AirQualityMeasurement] = None
    weather: Optional[WeatherData] = None
    predictions: List[AirQualityPrediction] = []
    active_alerts: List[Alert] = []


class ForecastResponse(BaseModel):
    """Forecast API response."""
    location: Location
    forecast_data: List[AirQualityPrediction]
    weather_forecast: List[WeatherData] = []
    confidence_metrics: Dict[str, float]


class HistoricalResponse(BaseModel):
    """Historical data API response."""
    location: Location
    measurements: List[AirQualityMeasurement]
    weather_data: List[WeatherData] = []
    start_date: datetime
    end_date: datetime
    total_records: int


# Query parameters
class AirQualityQuery(BaseModel):
    """Query parameters for air quality data."""
    location_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(10, ge=0.1, le=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    pollutant: Optional[str] = None
    source: Optional[DataSource] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v
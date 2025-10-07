"""
Data models for location API responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LocationFullResponse(BaseModel):
    """Complete location data response model"""
    
    name: str = Field(..., description="Location name")
    coordinates: List[float] = Field(..., description="[latitude, longitude]")
    aqi: int = Field(..., description="Air Quality Index")
    pm25: float = Field(..., description="PM2.5 concentration (µg/m³)")
    pm10: float = Field(..., description="PM10 concentration (µg/m³)")
    no2: float = Field(..., description="NO2 concentration (µg/m³)")
    o3: float = Field(..., description="O3 concentration (µg/m³)")
    so2: float = Field(..., description="SO2 concentration (µg/m³)")
    co: float = Field(..., description="CO concentration (mg/m³)")
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., description="Relative humidity (%)")
    windSpeed: float = Field(..., description="Wind speed (m/s)")
    windDirection: str = Field(..., description="Wind direction (N, NE, E, SE, S, SW, W, NW)")
    pressure: float = Field(..., description="Atmospheric pressure (hPa)")
    visibility: float = Field(..., description="Visibility (km)")
    lastUpdated: str = Field(..., description="Last update timestamp (ISO format)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Toronto, ON, Canada",
                "coordinates": [43.6532, -79.3832],
                "aqi": 42,
                "pm25": 8.5,
                "pm10": 15.2,
                "no2": 23.1,
                "o3": 65.4,
                "so2": 2.1,
                "co": 0.8,
                "temperature": 18.5,
                "humidity": 67.3,
                "windSpeed": 4.2,
                "windDirection": "SW",
                "pressure": 1013.2,
                "visibility": 10.0,
                "lastUpdated": "2025-10-07T15:30:00Z"
            }
        }

class AQIResponse(BaseModel):
    """Air Quality Index response model"""
    
    aqi: int = Field(..., description="Air Quality Index")
    category: str = Field(..., description="AQI category (Good, Moderate, etc.)")
    dominant_pollutant: str = Field(..., description="Main pollutant affecting AQI")
    last_updated: str = Field(..., description="Last update timestamp")

class PollutantData(BaseModel):
    """Individual pollutant data"""
    
    value: float = Field(..., description="Concentration value")
    unit: str = Field(..., description="Unit of measurement")
    aqi_contribution: Optional[int] = Field(None, description="Individual AQI for this pollutant")
    source: str = Field(..., description="Data source (NASA TEMPO, etc.)")

class PollutantsResponse(BaseModel):
    """Detailed pollutants response model"""
    
    pm25: PollutantData
    pm10: PollutantData
    no2: PollutantData
    o3: PollutantData
    so2: PollutantData
    co: PollutantData
    location: List[float] = Field(..., description="[latitude, longitude]")
    last_updated: str = Field(..., description="Last update timestamp")
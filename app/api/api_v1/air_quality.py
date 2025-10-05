"""
Air quality API endpoints.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.simple_schemas import (
    SimpleAirQualityResponse, SimpleForecastResponse, SimpleHistoricalResponse
)
from app.services.air_quality_service import AirQualityService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_air_quality_service() -> AirQualityService:
    """Dependency to get air quality service."""
    return AirQualityService()


@router.get("/current", response_model=SimpleAirQualityResponse)
async def get_current_air_quality(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(10, ge=0.1, le=100, description="Search radius in kilometers"),
    sources: Optional[List[str]] = Query(None, description="Data sources to include"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Get current air quality data for a location.
    
    - **latitude**: Location latitude (-90 to 90)
    - **longitude**: Location longitude (-180 to 180)
    - **radius_km**: Search radius in kilometers (0.1 to 100)
    - **sources**: Optional list of data sources (TEMPO, EPA, OpenAQ, etc.)
    
    Returns current air quality measurements, weather data, and active alerts.
    """
    try:
        result = await service.get_current_air_quality(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            sources=sources
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No air quality data found for the specified location"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting current air quality: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/forecast", response_model=SimpleForecastResponse)
async def get_air_quality_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    hours: int = Query(24, ge=1, le=168, description="Forecast horizon in hours"),
    model_version: Optional[str] = Query(None, description="Specific model version"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Get air quality forecast for a location.
    
    - **latitude**: Location latitude (-90 to 90)
    - **longitude**: Location longitude (-180 to 180)
    - **hours**: Forecast horizon in hours (1 to 168)
    - **model_version**: Optional specific model version to use
    
    Returns air quality predictions with confidence intervals.
    """
    try:
        result = await service.get_air_quality_forecast(
            latitude=latitude,
            longitude=longitude,
            hours=hours,
            model_version=model_version
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No forecast data available for the specified location"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting air quality forecast: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/historical", response_model=SimpleHistoricalResponse)
async def get_historical_air_quality(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    pollutant: Optional[str] = Query(None, description="Specific pollutant (pm25, no2, o3, etc.)"),
    sources: Optional[List[str]] = Query(None, description="Data sources to include"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Get historical air quality data for a location and time range.
    
    - **latitude**: Location latitude (-90 to 90)
    - **longitude**: Location longitude (-180 to 180)
    - **start_date**: Start of time range (ISO format)
    - **end_date**: End of time range (ISO format)
    - **pollutant**: Optional specific pollutant to filter
    - **sources**: Optional list of data sources to include
    - **limit**: Maximum number of records to return (1 to 10000)
    
    Returns historical measurements and weather data.
    """
    try:
        # Validate date range
        if end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date"
            )
        
        # Limit time range to prevent excessive queries
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise HTTPException(
                status_code=400,
                detail=f"Time range cannot exceed {max_days} days"
            )
        
        result = await service.get_historical_air_quality(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            pollutant=pollutant,
            sources=sources,
            limit=limit
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No historical data found for the specified criteria"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical air quality: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/aqi-info")
async def get_aqi_information():
    """
    Get information about Air Quality Index categories and health recommendations.
    
    Returns AQI categories, ranges, colors, and health advice.
    """
    return {
        "categories": [
            {
                "name": "Good",
                "range": "0-50",
                "color": "#00E400",
                "description": "Air quality is satisfactory",
                "health_advice": "Air quality is considered satisfactory, and air pollution poses little or no risk."
            },
            {
                "name": "Moderate", 
                "range": "51-100",
                "color": "#FFFF00",
                "description": "Air quality is acceptable",
                "health_advice": "Air quality is acceptable for most people. However, sensitive groups may experience minor to moderate symptoms."
            },
            {
                "name": "Unhealthy for Sensitive Groups",
                "range": "101-150", 
                "color": "#FF7E00",
                "description": "Members of sensitive groups may experience health effects",
                "health_advice": "Although general public is not likely to be affected, people with lung disease, older adults and children should consider reducing prolonged outdoor exertion."
            },
            {
                "name": "Unhealthy",
                "range": "151-200",
                "color": "#FF0000", 
                "description": "Everyone may begin to experience health effects",
                "health_advice": "People with lung disease, older adults and children should avoid prolonged outdoor exertion; everyone else should reduce prolonged outdoor exertion."
            },
            {
                "name": "Very Unhealthy",
                "range": "201-300",
                "color": "#8F3F97",
                "description": "Health warnings of emergency conditions",
                "health_advice": "People with lung disease, older adults and children should avoid all outdoor exertion; everyone else should avoid prolonged outdoor exertion."
            },
            {
                "name": "Hazardous",
                "range": "301-500",
                "color": "#7E0023", 
                "description": "Health alert: everyone may experience serious health effects",
                "health_advice": "Everyone should avoid all outdoor exertion."
            }
        ],
        "pollutants": {
            "PM2.5": {
                "name": "Fine Particulate Matter",
                "unit": "μg/m³",
                "description": "Particles smaller than 2.5 micrometers"
            },
            "PM10": {
                "name": "Coarse Particulate Matter", 
                "unit": "μg/m³",
                "description": "Particles smaller than 10 micrometers"
            },
            "NO2": {
                "name": "Nitrogen Dioxide",
                "unit": "ppb", 
                "description": "Gas produced by fuel combustion"
            },
            "O3": {
                "name": "Ground-level Ozone",
                "unit": "ppb",
                "description": "Gas formed by chemical reactions in sunlight"
            },
            "CO": {
                "name": "Carbon Monoxide",
                "unit": "ppm",
                "description": "Colorless, odorless gas from incomplete combustion"
            },
            "SO2": {
                "name": "Sulfur Dioxide", 
                "unit": "ppb",
                "description": "Gas produced by burning sulfur-containing fuels"
            }
        }
    }


@router.get("/by-state-province", response_model=SimpleAirQualityResponse)
async def get_air_quality_by_state_province(
    state_province: str = Query(..., description="State or Province name"),
    country: str = Query("USA", description="Country (USA or Canada)"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    🆕 NOUVELLE FONCTIONNALITÉ: Get air quality by State/Province
    
    - **state_province**: Name of the state or province (e.g., "California", "Ontario")
    - **country**: Country code ("USA" or "Canada")
    
    Returns air quality data for the geographic center of the state/province.
    """
    try:
        result = await service.get_air_quality_by_state_province(
            state_province=state_province,
            country=country
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No air quality data found for {state_province}, {country}"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting air quality for {state_province}, {country}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/location-details")
async def get_location_details(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    🆕 NOUVELLE FONCTIONNALITÉ: Get detailed geographic information
    
    - **latitude**: Location latitude (-90 to 90)
    - **longitude**: Location longitude (-180 to 180)
    
    Returns detailed geographic information including state/province identification.
    """
    try:
        result = await service.get_location_details(latitude, longitude)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Could not identify location details"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting location details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/air-quality-indices")
async def get_air_quality_indices(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    🆕 NOUVELLE FONCTIONNALITÉ: Get comprehensive air quality indices
    
    - **latitude**: Location latitude (-90 to 90)
    - **longitude**: Location longitude (-180 to 180)
    
    Returns EPA AQI, WHO compliance, and Canada AQHI indices.
    """
    try:
        result = await service.get_air_quality_indices(latitude, longitude)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="No air quality indices available for this location"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting air quality indices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/compare-regions")
async def compare_air_quality_regions(
    locations: List[Dict[str, Any]],
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    🆕 NOUVELLE FONCTIONNALITÉ: Compare air quality between multiple regions
    
    - **locations**: List of locations with latitude, longitude, and name
    
    Example:
    ```json
    [
        {"latitude": 34.0522, "longitude": -118.2437, "name": "Los Angeles"},
        {"latitude": 43.6532, "longitude": -79.3832, "name": "Toronto"}
    ]
    ```
    
    Returns comparison results with rankings and statistics.
    """
    try:
        # Convert to format expected by service
        location_tuples = []
        for loc in locations:
            if 'latitude' in loc and 'longitude' in loc and 'name' in loc:
                location_tuples.append((loc['latitude'], loc['longitude'], loc['name']))
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Each location must have 'latitude', 'longitude', and 'name' fields"
                )
        
        if len(location_tuples) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 locations are required for comparison"
            )
        
        result = await service.compare_air_quality_regions(location_tuples)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing air quality regions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/standards-info")
async def get_air_quality_standards_info():
    """
    🆕 NOUVELLE FONCTIONNALITÉ: Get information about air quality standards
    
    Returns detailed information about EPA AQI, WHO guidelines, and Canada AQHI.
    """
    return {
        "standards": {
            "EPA_AQI": {
                "name": "Environmental Protection Agency Air Quality Index",
                "country": "United States",
                "description": "Standard US air quality measurement scale",
                "scale": "0-500",
                "categories": [
                    {"name": "Good", "range": "0-50", "color": "#00E400"},
                    {"name": "Moderate", "range": "51-100", "color": "#FFFF00"},
                    {"name": "Unhealthy for Sensitive Groups", "range": "101-150", "color": "#FF7E00"},
                    {"name": "Unhealthy", "range": "151-200", "color": "#FF0000"},
                    {"name": "Very Unhealthy", "range": "201-300", "color": "#8F3F97"},
                    {"name": "Hazardous", "range": "301-500", "color": "#7E0023"}
                ]
            },
            "WHO": {
                "name": "World Health Organization Guidelines",
                "country": "Global",
                "description": "International health-based air quality guidelines",
                "guidelines_2021": {
                    "PM2.5": {"annual": "5 μg/m³", "24h": "15 μg/m³"},
                    "PM10": {"annual": "15 μg/m³", "24h": "45 μg/m³"},
                    "NO2": {"annual": "10 μg/m³", "1h": "25 μg/m³"},
                    "O3": {"peak_season": "60 μg/m³", "8h": "100 μg/m³"},
                    "SO2": {"24h": "40 μg/m³"}
                }
            },
            "AQHI_Canada": {
                "name": "Air Quality Health Index",
                "country": "Canada",
                "description": "Canadian health-based air quality scale",
                "scale": "1-10+",
                "categories": [
                    {"name": "Low Risk", "range": "1-3", "color": "#0099CC"},
                    {"name": "Moderate Risk", "range": "4-6", "color": "#FFFF00"},
                    {"name": "High Risk", "range": "7-10", "color": "#FF9900"},
                    {"name": "Very High Risk", "range": "10+", "color": "#FF0000"}
                ],
                "calculation": "Based on NO2, O3, and PM2.5 concentrations"
            }
        },
        "regional_coverage": {
            "North America": {
                "primary_standard": "EPA AQI",
                "canada_standard": "AQHI",
                "optimal_sources": ["NASA TEMPO", "EPA AirNow", "OpenAQ"]
            },
            "Europe": {
                "primary_standard": "WHO",
                "optimal_sources": ["ESA Sentinel-5P", "Sensor.Community", "OpenAQ"]
            },
            "Global": {
                "primary_standard": "WHO",
                "optimal_sources": ["NASA MERRA-2", "ESA Sentinel-5P", "OpenAQ"]
            }
        }
    }


@router.get("/north-america-states")
async def get_north_america_states_info():
    """
    🆕 NOUVELLE FONCTIONNALITÉ: Get information about North American states/provinces
    
    Returns database of US states and Canadian provinces with air quality monitoring.
    """
    return {
        "usa_states": [
            {"name": "California", "code": "CA", "major_cities": ["Los Angeles", "San Francisco", "San Diego"]},
            {"name": "Texas", "code": "TX", "major_cities": ["Houston", "Dallas", "Austin", "San Antonio"]},
            {"name": "Florida", "code": "FL", "major_cities": ["Miami", "Tampa", "Orlando", "Jacksonville"]},
            {"name": "New York", "code": "NY", "major_cities": ["New York City", "Buffalo", "Rochester"]},
            {"name": "Illinois", "code": "IL", "major_cities": ["Chicago", "Rockford", "Peoria"]},
            {"name": "Pennsylvania", "code": "PA", "major_cities": ["Philadelphia", "Pittsburgh", "Allentown"]},
            {"name": "Ohio", "code": "OH", "major_cities": ["Columbus", "Cleveland", "Cincinnati"]},
            {"name": "Georgia", "code": "GA", "major_cities": ["Atlanta", "Augusta", "Columbus"]},
            {"name": "North Carolina", "code": "NC", "major_cities": ["Charlotte", "Raleigh", "Greensboro"]},
            {"name": "Michigan", "code": "MI", "major_cities": ["Detroit", "Grand Rapids", "Warren"]}
        ],
        "canada_provinces": [
            {"name": "Ontario", "code": "ON", "major_cities": ["Toronto", "Ottawa", "Hamilton"]},
            {"name": "Quebec", "code": "QC", "major_cities": ["Montreal", "Quebec City", "Laval"]},
            {"name": "British Columbia", "code": "BC", "major_cities": ["Vancouver", "Victoria", "Surrey"]},
            {"name": "Alberta", "code": "AB", "major_cities": ["Calgary", "Edmonton", "Red Deer"]},
            {"name": "Manitoba", "code": "MB", "major_cities": ["Winnipeg", "Brandon", "Steinbach"]},
            {"name": "Saskatchewan", "code": "SK", "major_cities": ["Saskatoon", "Regina", "Prince Albert"]}
        ],
        "coverage_info": {
            "nasa_tempo": "Optimal coverage for all North American locations",
            "data_sources": "NASA TEMPO + EPA AirNow + OpenAQ + AQICN",
            "standards": "EPA AQI for USA, AQHI for Canada",
            "update_frequency": "Real-time and daily averages available"
        }
    }


@router.get("/compare-sources")
async def compare_data_sources(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    pollutant: str = Query("pm25", description="Pollutant to compare"),
    hours: int = Query(24, ge=1, le=72, description="Time window in hours"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Compare air quality data from different sources for validation.
    
    - **latitude**: Location latitude (-90 to 90)
    - **longitude**: Location longitude (-180 to 180) 
    - **pollutant**: Pollutant to compare (pm25, no2, o3, etc.)
    - **hours**: Time window for comparison in hours (1 to 72)
    
    Returns comparison of measurements from satellite vs ground sources.
    """
    try:
        result = await service.compare_data_sources(
            latitude=latitude,
            longitude=longitude,
            pollutant=pollutant,
            hours=hours
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing data sources: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
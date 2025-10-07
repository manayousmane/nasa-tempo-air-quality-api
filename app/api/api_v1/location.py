"""
Location API endpoints for NASA TEMPO air quality data
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import asyncio
from datetime import datetime

from app.services.nasa_tempo_service import NASATempoService
from app.models.location_models import LocationFullResponse

router = APIRouter()

# Initialize NASA TEMPO service
nasa_service = NASATempoService()

@router.get("/full", response_model=LocationFullResponse)
async def get_location_full_data(
    latitude: float,
    longitude: float
) -> Dict[str, Any]:
    """
    Get complete air quality and weather data for a location
    
    Args:
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
    
    Returns:
        Complete location data including air quality and weather
    """
    
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
    
    try:
        # Get data from NASA TEMPO and other sources
        location_data = await nasa_service.get_complete_location_data(latitude, longitude)
        
        return location_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving location data: {str(e)}"
        )

@router.get("/aqi", response_model=Dict[str, Any])
async def get_location_aqi(
    latitude: float,
    longitude: float
) -> Dict[str, Any]:
    """
    Get Air Quality Index for a location
    """
    
    try:
        aqi_data = await nasa_service.get_aqi_data(latitude, longitude)
        return aqi_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving AQI data: {str(e)}"
        )

@router.get("/pollutants", response_model=Dict[str, Any])
async def get_location_pollutants(
    latitude: float,
    longitude: float
) -> Dict[str, Any]:
    """
    Get detailed pollutant concentrations for a location
    """
    
    try:
        pollutant_data = await nasa_service.get_pollutant_data(latitude, longitude)
        return pollutant_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pollutant data: {str(e)}"
        )
"""
Location management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.schemas import Location, LocationCreate
from app.services.location_service import LocationService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_location_service() -> LocationService:
    """Dependency to get location service."""
    return LocationService()


@router.get("/", response_model=List[Location])
async def get_locations(
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state/province"),
    active_only: bool = Query(True, description="Only return active locations"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of locations"),
    service: LocationService = Depends(get_location_service)
):
    """
    Get list of available monitoring locations.
    
    - **country**: Filter locations by country
    - **state**: Filter locations by state/province
    - **active_only**: Only return active monitoring locations
    - **limit**: Maximum number of locations to return (1 to 1000)
    
    Returns list of monitoring locations with coordinates and metadata.
    """
    try:
        locations = await service.get_locations(
            country=country,
            state=state,
            active_only=active_only,
            limit=limit
        )
        
        return locations
        
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{location_id}", response_model=Location)
async def get_location(
    location_id: int,
    service: LocationService = Depends(get_location_service)
):
    """
    Get detailed information about a specific location.
    
    - **location_id**: Unique location identifier
    
    Returns detailed location information including recent data availability.
    """
    try:
        location = await service.get_location(location_id)
        
        if not location:
            raise HTTPException(
                status_code=404,
                detail="Location not found"
            )
        
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location {location_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/nearby")
async def find_nearby_locations(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(50, ge=0.1, le=500, description="Search radius in kilometers"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of locations"),
    service: LocationService = Depends(get_location_service)
):
    """
    Find monitoring locations near a point.
    
    - **latitude**: Search center latitude (-90 to 90)
    - **longitude**: Search center longitude (-180 to 180)
    - **radius_km**: Search radius in kilometers (0.1 to 500)
    - **limit**: Maximum number of locations to return (1 to 100)
    
    Returns nearby monitoring locations sorted by distance.
    """
    try:
        locations = await service.find_nearby_locations(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit
        )
        
        return {
            "search_center": {"latitude": latitude, "longitude": longitude},
            "search_radius_km": radius_km,
            "total_found": len(locations),
            "locations": locations
        }
        
    except Exception as e:
        logger.error(f"Error finding nearby locations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=Location)
async def create_location(
    location_data: LocationCreate,
    service: LocationService = Depends(get_location_service)
):
    """
    Create a new monitoring location.
    
    - **location_data**: Location information including name, coordinates, and metadata
    
    Returns the created location with assigned ID.
    
    Note: This endpoint is typically used for administrative purposes.
    """
    try:
        # Check if location already exists
        existing = await service.find_nearby_locations(
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            radius_km=1.0,  # Within 1km
            limit=1
        )
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="A location already exists within 1km of these coordinates"
            )
        
        location = await service.create_location(location_data)
        return location
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/coverage/global")
async def get_global_coverage(
    service: LocationService = Depends(get_location_service)
):
    """
    Get global coverage statistics and data availability.
    
    Returns coverage information by region, data source availability,
    and monitoring network statistics.
    """
    try:
        coverage = await service.get_global_coverage()
        return coverage
        
    except Exception as e:
        logger.error(f"Error getting global coverage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/data-sources/{location_id}")
async def get_location_data_sources(
    location_id: int,
    service: LocationService = Depends(get_location_service)
):
    """
    Get available data sources for a specific location.
    
    - **location_id**: Unique location identifier
    
    Returns list of data sources available at this location with
    update frequencies and data quality information.
    """
    try:
        location = await service.get_location(location_id)
        if not location:
            raise HTTPException(
                status_code=404,
                detail="Location not found"
            )
        
        data_sources = await service.get_location_data_sources(location_id)
        return {
            "location": location,
            "data_sources": data_sources
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data sources for location {location_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
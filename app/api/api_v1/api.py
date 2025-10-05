"""
API router configuration.
"""
from fastapi import APIRouter

from app.api.api_v1 import air_quality, locations, alerts, enhanced_endpoints, monitoring, geolocation, tempo_predictions, location_search, location_data

api_router = APIRouter()

# Include all route modules
api_router.include_router(air_quality.router, prefix="/air-quality", tags=["Air Quality"])
api_router.include_router(enhanced_endpoints.router, prefix="/air-quality", tags=["Enhanced Air Quality"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring & Performance"])
api_router.include_router(geolocation.router, prefix="/geolocation", tags=["Geolocation & Location Intelligence"])
api_router.include_router(tempo_predictions.router, prefix="/tempo", tags=["🛰️ TEMPO ML Predictions"])
api_router.include_router(location_search.router, prefix="/location-search", tags=["🌍 Location Search by Name"])
api_router.include_router(location_data.router, prefix="/location", tags=["📍 Location Data"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
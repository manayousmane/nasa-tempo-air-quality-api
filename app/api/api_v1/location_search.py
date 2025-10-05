"""
🌍 API LOCALISATION PAR NOM
================================================================================
Endpoints pour rechercher qualité de l'air par nom de pays/état/province/ville
================================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.services.location_geocoding_service import location_service, LocationData
from app.services.tempo_model_service import TempoModelService

logger = logging.getLogger(__name__)

# Instance du service TEMPO
tempo_service = TempoModelService()

router = APIRouter()

# ================================================================================
# MODÈLES PYDANTIC
# ================================================================================

class LocationSearchRequest(BaseModel):
    """Requête de recherche par nom de lieu"""
    location_name: str = Field(..., min_length=2, max_length=100, description="Nom du pays, état, province ou ville")
    include_predictions: Optional[bool] = Field(True, description="Inclure les prédictions air quality")

class LocationSearchResponse(BaseModel):
    """Réponse de recherche par localisation"""
    success: bool
    location_found: bool
    location_info: Optional[Dict[str, Any]]
    air_quality_data: Optional[LocationData]
    timestamp: datetime
    error: Optional[str] = None

class LocationSuggestionsResponse(BaseModel):
    """Réponse avec suggestions de locations"""
    query: str
    suggestions: List[str]
    total_available: int

class MultiLocationRequest(BaseModel):
    """Requête pour plusieurs locations"""
    location_names: List[str] = Field(..., max_items=10, description="Maximum 10 locations")
    include_predictions: Optional[bool] = Field(True, description="Inclure les prédictions")

# ================================================================================
# ENDPOINTS API
# ================================================================================

@router.get("/available-locations", response_model=Dict[str, Any])
async def get_available_locations():
    """
    📍 Liste toutes les locations disponibles en Amérique du Nord
    """
    try:
        locations = location_service.get_all_available_locations()
        
        # Grouper par pays
        grouped = {}
        for loc in locations:
            country = loc["country"]
            if country not in grouped:
                grouped[country] = {}
            
            state = loc["state"] or "National"
            if state not in grouped[country]:
                grouped[country][state] = []
            
            grouped[country][state].append({
                "name": loc["name"],
                "coordinates": loc["coordinates"],
                "in_tempo_coverage": loc["in_tempo_coverage"]
            })
        
        return {
            "service": "TEMPO Location Database",
            "total_locations": len(locations),
            "coverage_note": "Only North America (TEMPO satellite coverage)",
            "locations_by_country": grouped,
            "supported_types": [
                "Countries (United States, Canada)",
                "States/Provinces (California, Ontario, Texas, Quebec, etc.)",
                "Major Cities (New York, Toronto, Los Angeles, Vancouver, etc.)"
            ]
        }
        
    except Exception as e:
        logger.error(f"Erreur liste locations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération locations: {str(e)}")

@router.get("/suggest", response_model=LocationSuggestionsResponse)
async def suggest_locations(
    q: str = Query(..., min_length=1, max_length=50, description="Début du nom de lieu")
):
    """
    🔍 Suggestions de locations basées sur une requête partielle
    
    Exemple: /suggest?q=new → ["New York", "New Jersey", ...]
    """
    try:
        suggestions = location_service.get_suggested_locations(q)
        all_locations = location_service.get_all_available_locations()
        
        return LocationSuggestionsResponse(
            query=q,
            suggestions=suggestions,
            total_available=len(all_locations)
        )
        
    except Exception as e:
        logger.error(f"Erreur suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur suggestions: {str(e)}")

@router.post("/search", response_model=LocationSearchResponse)
async def search_by_location_name(request: LocationSearchRequest):
    """
    🎯 Recherche qualité de l'air par nom de lieu
    
    Supporte:
    - Pays: "United States", "Canada"
    - États/Provinces: "California", "Ontario", "Texas", "Quebec"
    - Villes: "New York", "Toronto", "Los Angeles", "Vancouver"
    """
    try:
        # Géocodage de la location
        location_info = await location_service.geocode_location(request.location_name)
        
        if not location_info:
            return LocationSearchResponse(
                success=True,
                location_found=False,
                location_info=None,
                air_quality_data=None,
                timestamp=datetime.now(),
                error=f"Location '{request.location_name}' non trouvée ou hors zone TEMPO"
            )
        
        # Vérifier coverage TEMPO
        lat, lon = location_info["latitude"], location_info["longitude"]
        if not location_service.is_in_tempo_coverage(lat, lon):
            return LocationSearchResponse(
                success=True,
                location_found=True,
                location_info=location_info,
                air_quality_data=None,
                timestamp=datetime.now(),
                error="Location trouvée mais hors de la zone de couverture TEMPO (40°N-70°N, 70°W-130°W)"
            )
        
        # Prédictions air quality si demandées
        air_quality_data = None
        if request.include_predictions and tempo_service.is_loaded:
            try:
                coordinates = {"latitude": lat, "longitude": lon}
                features = {}  # Utiliser valeurs par défaut
                
                predictions = tempo_service.predict_all_pollutants(coordinates, features)
                aqi = tempo_service.calculate_aqi(predictions)
                
                # Construire LocationData
                air_quality_data = LocationData(
                    name=location_info["name"],
                    coordinates=[lat, lon],
                    aqi=aqi.get("overall"),
                    pm25=predictions.get("pm25"),
                    pm10=predictions.get("pm10"),
                    no2=predictions.get("no2"),
                    o3=predictions.get("o3"),
                    so2=predictions.get("so2"),
                    co=predictions.get("co"),
                    # Météo par défaut (pourrait être enrichi)
                    temperature=15.0,
                    humidity=65.0,
                    wind_speed=5.0,
                    wind_direction="SW",
                    pressure=1013.25,
                    visibility=10.0,
                    last_updated=datetime.now().isoformat()
                )
                
            except Exception as e:
                logger.error(f"Erreur prédictions pour {request.location_name}: {str(e)}")
                # Continuer sans prédictions
        
        return LocationSearchResponse(
            success=True,
            location_found=True,
            location_info=location_info,
            air_quality_data=air_quality_data,
            timestamp=datetime.now(),
            error=None
        )
        
    except Exception as e:
        logger.error(f"Erreur recherche {request.location_name}: {str(e)}")
        return LocationSearchResponse(
            success=False,
            location_found=False,
            location_info=None,
            air_quality_data=None,
            timestamp=datetime.now(),
            error=str(e)
        )

@router.post("/search-multiple", response_model=Dict[str, Any])
async def search_multiple_locations(request: MultiLocationRequest):
    """
    📊 Recherche qualité de l'air pour plusieurs lieux simultanément
    
    Maximum 10 locations par requête.
    """
    try:
        if len(request.location_names) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 locations par requête")
        
        results = []
        
        for location_name in request.location_names:
            try:
                # Géocodage
                location_info = await location_service.geocode_location(location_name)
                
                result = {
                    "query": location_name,
                    "found": False,
                    "location_info": None,
                    "air_quality_data": None,
                    "error": None
                }
                
                if location_info:
                    result["found"] = True
                    result["location_info"] = location_info
                    
                    # Prédictions si demandées et dans zone TEMPO
                    lat, lon = location_info["latitude"], location_info["longitude"]
                    if (request.include_predictions and 
                        tempo_service.is_loaded and 
                        location_service.is_in_tempo_coverage(lat, lon)):
                        
                        try:
                            coordinates = {"latitude": lat, "longitude": lon}
                            predictions = tempo_service.predict_all_pollutants(coordinates, {})
                            aqi = tempo_service.calculate_aqi(predictions)
                            
                            result["air_quality_data"] = {
                                "aqi": aqi.get("overall"),
                                "pm25": predictions.get("pm25"),
                                "pm10": predictions.get("pm10"),
                                "no2": predictions.get("no2"),
                                "o3": predictions.get("o3"),
                                "co": predictions.get("co"),
                                "so2": predictions.get("so2"),
                                "last_updated": datetime.now().isoformat()
                            }
                            
                        except Exception as e:
                            result["error"] = f"Erreur prédictions: {str(e)}"
                else:
                    result["error"] = "Location non trouvée ou hors zone TEMPO"
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    "query": location_name,
                    "found": False,
                    "location_info": None,
                    "air_quality_data": None,
                    "error": str(e)
                })
        
        # Statistiques
        found_count = sum(1 for r in results if r["found"])
        with_predictions = sum(1 for r in results if r["air_quality_data"] is not None)
        
        return {
            "batch_summary": {
                "total_queries": len(request.location_names),
                "locations_found": found_count,
                "with_air_quality": with_predictions,
                "success_rate": found_count / len(request.location_names)
            },
            "results": results,
            "timestamp": datetime.now(),
            "note": "Only North America locations with TEMPO coverage provide air quality predictions"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur batch search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur batch search: {str(e)}")

@router.get("/health")
async def location_service_health():
    """
    ❤️ Vérification santé du service de localisation
    """
    try:
        total_locations = len(location_service.get_all_available_locations())
        tempo_coverage = sum(1 for loc in location_service.get_all_available_locations() 
                           if loc["in_tempo_coverage"])
        
        return {
            "status": "healthy",
            "total_locations": total_locations,
            "tempo_coverage_locations": tempo_coverage,
            "geocoding_service": "nominatim + local_database",
            "prediction_service": "operational" if tempo_service.is_loaded else "unavailable"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
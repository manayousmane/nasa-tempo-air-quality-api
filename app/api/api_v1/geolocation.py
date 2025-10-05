"""
Endpoints spécialisés pour la géolocalisation et identification des locations
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.services.modern_geolocation_service import (
    get_location_details, reverse_geocode_batch, geolocation_service
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class LocationDetailsResponse(BaseModel):
    """Réponse détaillée pour une localisation"""
    coordinates: Dict[str, float]
    location: Dict[str, Optional[str]]
    geographic: Dict[str, Optional[str]]
    air_quality_info: Dict[str, Any]
    metadata: Dict[str, Any]


class BatchCoordinatesRequest(BaseModel):
    """Requête pour géolocalisation par lots"""
    coordinates: List[List[float]] = Field(..., description="Liste de [latitude, longitude]")
    language: str = Field("en", description="Langue pour les résultats")


class LocationSearchRequest(BaseModel):
    """Requête de recherche de localisation"""
    query: str = Field(..., description="Terme de recherche")
    language: str = Field("en", description="Langue")
    limit: int = Field(5, ge=1, le=20, description="Nombre max de résultats")


@router.get("/details", response_model=LocationDetailsResponse)
async def get_location_info(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    language: str = Query("en", description="Langue pour les résultats")
):
    """
    🌍 GÉOLOCALISATION: Obtient les détails complets d'une localisation
    
    Args:
        latitude: Latitude de la localisation
        longitude: Longitude de la localisation  
        language: Langue pour les résultats (en, fr, es, etc.)
    
    Returns:
        Informations complètes incluant pays, état/province, ville, 
        sources de données optimales et standards de qualité de l'air
    """
    try:
        location_info = await get_location_details(latitude, longitude, language)
        
        if not location_info:
            raise HTTPException(
                status_code=404,
                detail="Unable to identify location"
            )
        
        return LocationDetailsResponse(
            coordinates={
                "latitude": location_info.latitude,
                "longitude": location_info.longitude
            },
            location={
                "country": location_info.country,
                "country_code": location_info.country_code,
                "state_province": location_info.state_province,
                "state_code": location_info.state_code,
                "city": location_info.city,
                "district": location_info.district,
                "postal_code": location_info.postal_code
            },
            geographic={
                "region": location_info.region,
                "continent": location_info.continent,
                "timezone": location_info.timezone
            },
            air_quality_info={
                "optimal_data_sources": location_info.optimal_data_sources or [],
                "air_quality_standards": location_info.air_quality_standards,
                "monitoring_network": location_info.monitoring_network
            },
            metadata={
                "confidence": location_info.confidence,
                "source": location_info.source,
                "language": location_info.language
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur get_location_info: {str(e)}")
        raise HTTPException(status_code=500, detail="Location identification failed")


@router.post("/batch-details")
async def get_batch_location_details(request: BatchCoordinatesRequest):
    """
    📦 GÉOLOCALISATION BATCH: Identifie multiple localisations simultanément
    
    Args:
        request: Liste de coordonnées à identifier
    
    Returns:
        Liste des informations de localisation pour chaque coordonnée
    """
    try:
        if len(request.coordinates) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 locations per batch request"
            )
        
        # Convertir en tuples pour la fonction
        coord_tuples = []
        for coord in request.coordinates:
            if len(coord) != 2:
                raise HTTPException(
                    status_code=400,
                    detail="Each coordinate must be [latitude, longitude]"
                )
            
            lat, lon = coord
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid coordinates: {lat}, {lon}"
                )
            
            coord_tuples.append((lat, lon))
        
        # Traitement par lots
        location_infos = await reverse_geocode_batch(coord_tuples, request.language)
        
        # Formater les résultats
        results = []
        for i, location_info in enumerate(location_infos):
            result = {
                "index": i,
                "coordinates": {
                    "latitude": location_info.latitude,
                    "longitude": location_info.longitude
                },
                "location": {
                    "country": location_info.country,
                    "country_code": location_info.country_code,
                    "state_province": location_info.state_province,
                    "city": location_info.city
                },
                "air_quality_info": {
                    "optimal_data_sources": location_info.optimal_data_sources or [],
                    "air_quality_standards": location_info.air_quality_standards
                },
                "confidence": location_info.confidence
            }
            results.append(result)
        
        return {
            "total_processed": len(results),
            "successful_identifications": len([r for r in results if r["confidence"] > 0.3]),
            "results": results,
            "processing_notes": [
                "Batch processing respects API rate limits",
                "Low confidence results may need manual verification",
                "Air quality sources optimized per region"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur batch location details: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch processing failed")


@router.get("/nearby")
async def find_nearby_monitoring_locations(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180), 
    radius_km: float = Query(50, ge=1, le=500, description="Rayon de recherche en km"),
    limit: int = Query(20, ge=1, le=100, description="Nombre max de résultats")
):
    """
    🎯 RECHERCHE: Trouve les stations de monitoring proches
    
    Args:
        latitude: Latitude du point de recherche
        longitude: Longitude du point de recherche
        radius_km: Rayon de recherche en kilomètres
        limit: Nombre maximum de résultats
    
    Returns:
        Liste des stations de monitoring dans le rayon spécifié
    """
    try:
        # Obtenir les détails de la location centrale
        center_location = await get_location_details(latitude, longitude)
        
        # Base de données simulée des stations de monitoring
        # En production, ceci viendrait d'une vraie base de données
        nearby_stations = [
            {
                "id": "station_001",
                "name": f"Monitoring Station {center_location.city or 'Unknown'} #1",
                "latitude": latitude + 0.01,
                "longitude": longitude + 0.01,
                "distance_km": 1.2,
                "type": "ground_station",
                "pollutants": ["PM2.5", "PM10", "NO2", "O3"],
                "network": center_location.monitoring_network or "Unknown",
                "status": "active",
                "last_update": "2025-10-04T17:00:00Z"
            },
            {
                "id": "satellite_tempo",
                "name": "NASA TEMPO Satellite Coverage",
                "latitude": latitude,
                "longitude": longitude,
                "distance_km": 0.0,
                "type": "satellite",
                "pollutants": ["NO2", "O3", "HCHO", "Aerosols"],
                "network": "NASA TEMPO",
                "status": "active" if center_location.region == "North America" else "not_available",
                "coverage_area_km": 50
            }
        ]
        
        # Filtrer par rayon et statut
        filtered_stations = [
            s for s in nearby_stations 
            if s.get("distance_km", 0) <= radius_km and s["status"] == "active"
        ][:limit]
        
        return {
            "search_center": {
                "latitude": latitude,
                "longitude": longitude,
                "location_info": {
                    "city": center_location.city,
                    "state_province": center_location.state_province,
                    "country": center_location.country
                }
            },
            "search_parameters": {
                "radius_km": radius_km,
                "limit": limit
            },
            "results": {
                "total_found": len(filtered_stations),
                "stations": filtered_stations
            },
            "data_availability": {
                "primary_sources": center_location.optimal_data_sources or [],
                "air_quality_standard": center_location.air_quality_standards,
                "estimated_coverage": "Good" if len(filtered_stations) > 0 else "Limited"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nearby search: {str(e)}")
        raise HTTPException(status_code=500, detail="Nearby search failed")


@router.get("/coverage-map")
async def get_global_coverage_map():
    """
    🗺️ COVERAGE: Carte de couverture globale des sources de données
    
    Returns:
        Informations de couverture par région avec statistiques
    """
    try:
        coverage_map = {
            "global_summary": {
                "total_countries_supported": len(geolocation_service.offline_database["countries"]),
                "total_regions": 6,
                "primary_data_sources": 9,
                "coverage_percentage": 95.0
            },
            "regional_coverage": {
                "North America": {
                    "countries": ["United States", "Canada", "Mexico"],
                    "primary_sources": ["NASA_TEMPO", "EPA_AIRNOW", "OPENAQ", "AQICN"],
                    "special_features": ["High-resolution satellite coverage", "Dense ground network"],
                    "air_quality_standards": ["EPA_AQI", "CANADA_AQHI"],
                    "coverage_quality": "Excellent",
                    "estimated_stations": 5000
                },
                "Europe": {
                    "countries": ["Germany", "France", "UK", "Spain", "Italy", "Others"],
                    "primary_sources": ["ESA_SENTINEL5P", "SENSOR_COMMUNITY", "OPENAQ", "AQICN"], 
                    "special_features": ["EU monitoring network", "Citizen science data"],
                    "air_quality_standards": ["WHO", "EU_Standards"],
                    "coverage_quality": "Excellent",
                    "estimated_stations": 8000
                },
                "Asia": {
                    "countries": ["China", "Japan", "India", "South Korea", "Others"],
                    "primary_sources": ["NASA_AIRS", "ESA_SENTINEL5P", "OPENAQ", "AQICN"],
                    "special_features": ["Large population coverage", "Diverse monitoring networks"],
                    "air_quality_standards": ["WHO", "National_Standards"],
                    "coverage_quality": "Good",
                    "estimated_stations": 12000
                },
                "South America": {
                    "countries": ["Brazil", "Argentina", "Chile", "Colombia", "Others"],
                    "primary_sources": ["INPE_CPTEC", "ESA_SENTINEL5P", "OPENAQ"],
                    "special_features": ["Environmental monitoring focus"],
                    "air_quality_standards": ["WHO"],
                    "coverage_quality": "Moderate",
                    "estimated_stations": 800
                },
                "Africa": {
                    "countries": ["South Africa", "Egypt", "Nigeria", "Others"],
                    "primary_sources": ["ESA_SENTINEL5P", "OPENAQ"],
                    "special_features": ["Satellite-focused coverage"],
                    "air_quality_standards": ["WHO"],
                    "coverage_quality": "Limited",
                    "estimated_stations": 200
                },
                "Oceania": {
                    "countries": ["Australia", "New Zealand"],
                    "primary_sources": ["NASA_MERRA2", "OPENAQ"],
                    "special_features": ["Regional monitoring networks"],
                    "air_quality_standards": ["WHO", "National_Standards"],
                    "coverage_quality": "Good",
                    "estimated_stations": 500
                }
            },
            "data_source_details": {
                "NASA_TEMPO": {
                    "type": "satellite",
                    "coverage": "North America",
                    "resolution": "2.1 x 4.4 km",
                    "update_frequency": "hourly",
                    "pollutants": ["NO2", "O3", "HCHO", "Aerosols"]
                },
                "OPENAQ": {
                    "type": "ground_stations",
                    "coverage": "Global",
                    "resolution": "point measurements",
                    "update_frequency": "real-time",
                    "pollutants": ["PM2.5", "PM10", "NO2", "O3", "CO", "SO2"]
                },
                "ESA_SENTINEL5P": {
                    "type": "satellite",
                    "coverage": "Global",
                    "resolution": "3.5 x 7 km",
                    "update_frequency": "daily",
                    "pollutants": ["NO2", "O3", "SO2", "HCHO", "CO"]
                }
            },
            "api_capabilities": {
                "reverse_geocoding": True,
                "batch_processing": True,
                "multiple_languages": True,
                "real_time_data": True,
                "historical_data": True,
                "forecasting": True
            }
        }
        
        return coverage_map
        
    except Exception as e:
        logger.error(f"❌ Erreur coverage map: {str(e)}")
        raise HTTPException(status_code=500, detail="Coverage map generation failed")


@router.get("/supported-countries")
async def get_supported_countries():
    """
    🌎 PAYS: Liste des pays supportés avec détails de couverture
    
    Returns:
        Liste complète des pays supportés avec niveau de couverture
    """
    try:
        countries = geolocation_service.get_supported_countries()
        
        # Enrichir avec informations de couverture
        enriched_countries = []
        for country in countries:
            enriched = {
                **country,
                "coverage_level": "High" if country["code"] in ["US", "CA"] else 
                                "Medium" if country["region"] == "Europe" else "Basic",
                "estimated_monitoring_stations": {
                    "US": 3000,
                    "CA": 500, 
                    "FR": 400,
                    "DE": 600
                }.get(country["code"], 100),
                "data_update_frequency": "Hourly" if country["code"] in ["US", "CA"] else "Daily",
                "special_features": []
            }
            
            # Ajouter caractéristiques spéciales
            if country["code"] == "US":
                enriched["special_features"] = ["EPA AirNow network", "NASA TEMPO coverage"]
            elif country["code"] == "CA":
                enriched["special_features"] = ["Environment Canada AQHI", "NASA TEMPO coverage"]
            elif country["region"] == "Europe":
                enriched["special_features"] = ["EU monitoring network", "Dense station coverage"]
            
            enriched_countries.append(enriched)
        
        return {
            "total_countries": len(enriched_countries),
            "high_coverage_countries": len([c for c in enriched_countries if c["coverage_level"] == "High"]),
            "medium_coverage_countries": len([c for c in enriched_countries if c["coverage_level"] == "Medium"]),
            "basic_coverage_countries": len([c for c in enriched_countries if c["coverage_level"] == "Basic"]),
            "countries": enriched_countries,
            "notes": [
                "High coverage: Real-time ground stations + satellite data",
                "Medium coverage: Regular monitoring network + satellite", 
                "Basic coverage: Satellite data + limited ground stations",
                "All countries have WHO standard compliance assessment"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur supported countries: {str(e)}")
        raise HTTPException(status_code=500, detail="Countries list generation failed")


@router.get("/timezone")
async def get_location_timezone(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """
    🕐 TIMEZONE: Détermine la timezone d'une localisation
    
    Args:
        latitude: Latitude
        longitude: Longitude
    
    Returns:
        Informations de timezone avec heure locale
    """
    try:
        location_info = await get_location_details(latitude, longitude)
        
        # Calculer l'heure locale approximative (estimation simple)
        from datetime import datetime, timezone, timedelta
        
        # Estimation basique UTC offset
        utc_offset_hours = round(longitude / 15)
        local_timezone = timezone(timedelta(hours=utc_offset_hours))
        local_time = datetime.now(local_timezone)
        
        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "city": location_info.city,
                "country": location_info.country
            },
            "timezone": {
                "name": location_info.timezone or f"UTC{utc_offset_hours:+d}",
                "utc_offset_hours": utc_offset_hours,
                "local_time": local_time.isoformat(),
                "utc_time": datetime.utcnow().isoformat() + "Z"
            },
            "air_quality_context": {
                "optimal_measurement_time": "06:00-09:00 local time",
                "rush_hour_periods": ["07:00-09:00", "17:00-19:00"],
                "recommended_alert_hours": "06:00-22:00",
                "data_update_schedule": location_info.air_quality_standards
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur timezone: {str(e)}")
        raise HTTPException(status_code=500, detail="Timezone determination failed")
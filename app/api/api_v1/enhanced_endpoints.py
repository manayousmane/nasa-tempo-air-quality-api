"""
Nouveaux endpoints API pour États/Provinces et indices détaillés
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel

from app.services.air_quality_service import AirQualityService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Modèles de réponse
class StateAirQualityResponse(BaseModel):
    """Réponse qualité air pour un État/Province"""
    state: str
    city: str
    country: str
    coordinates: Dict[str, float]
    timestamp: str
    epa_aqi_global: int
    epa_category_global: str
    canada_aqhi: Optional[float] = None
    canada_aqhi_category: Optional[str] = None
    pollutant_indices: List[Dict[str, Any]]
    data_sources: List[str]


class AirQualityIndicesResponse(BaseModel):
    """Réponse indices détaillés EPA/WHO/AQHI"""
    location: Dict[str, float]
    region: str
    timestamp: str
    indices_detail: List[Dict[str, Any]]
    summary: Dict[str, Any]


def get_air_quality_service() -> AirQualityService:
    """Dependency to get air quality service."""
    return AirQualityService()


@router.get("/states/list", response_model=List[str])
async def list_available_states():
    """Liste des États/Provinces disponibles"""
    try:
        service = AirQualityService()
        states = list(service.north_america_tester.north_america_locations.keys())
        logger.info(f"📋 Liste États/Provinces: {len(states)} disponibles")
        return states
    except Exception as e:
        logger.error(f"❌ Erreur liste États: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur récupération liste États")


@router.get("/states/{state_name}", response_model=StateAirQualityResponse)
async def get_state_air_quality(
    state_name: str = Path(..., description="Nom de l'État ou Province"),
    country: str = Query("USA", description="Pays (USA ou Canada)"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Obtenir la qualité de l'air pour un État/Province spécifique
    avec indices EPA AQI + WHO + Canada AQHI détaillés
    """
    try:
        logger.info(f"🏛️ Requête État: {state_name}, {country}")
        
        result = await service.get_state_air_quality(state_name, country)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"État/Province '{state_name}' non trouvé. Utilisez /states/list pour voir les options disponibles."
            )
        
        response = StateAirQualityResponse(**result)
        logger.info(f"✅ Données État retournées: AQI {result.get('epa_aqi_global')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur État {state_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne serveur")


@router.get("/provinces/{province_name}", response_model=StateAirQualityResponse)
async def get_province_air_quality(
    province_name: str = Path(..., description="Nom de la Province canadienne"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Obtenir la qualité de l'air pour une Province canadienne
    avec Canada AQHI détaillé
    """
    try:
        logger.info(f"🇨🇦 Requête Province: {province_name}")
        
        result = await service.get_state_air_quality(province_name, "Canada")
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Province '{province_name}' non trouvée. Utilisez /states/list pour voir les options disponibles."
            )
        
        response = StateAirQualityResponse(**result)
        logger.info(f"✅ Données Province retournées: AQHI {result.get('canada_aqhi')}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur Province {province_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne serveur")


@router.get("/indices", response_model=AirQualityIndicesResponse)
async def get_air_quality_indices(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude"),
    service: AirQualityService = Depends(get_air_quality_service)
):
    """
    Obtenir tous les indices de qualité de l'air (EPA AQI, WHO, Canada AQHI)
    avec détail par polluant et recommandations santé
    """
    try:
        logger.info(f"📊 Requête indices: {latitude:.4f}, {longitude:.4f}")
        
        result = await service.get_air_quality_indices(latitude, longitude)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Aucune donnée d'indices disponible pour cette localisation"
            )
        
        response = AirQualityIndicesResponse(**result)
        logger.info(f"✅ Indices retournés: {result.get('summary', {}).get('pollutants_count', 0)} polluants")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur indices: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur calcul indices")


@router.get("/regions")
async def get_supported_regions():
    """Liste des régions supportées avec leurs spécialisations"""
    return {
        "regions": {
            "North America": {
                "description": "États-Unis - Couverture optimale NASA TEMPO",
                "specializations": ["NASA TEMPO", "EPA AirNow", "AIRS"],
                "indices": ["EPA AQI", "WHO Standards"],
                "states_count": 10
            },
            "Canada": {
                "description": "Provinces canadiennes - Indices AQHI spécialisés", 
                "specializations": ["CSA OSIRIS", "Canada AQHI", "TEMPO"],
                "indices": ["Canada AQHI", "EPA AQI", "WHO Standards"],
                "provinces_count": 6
            },
            "Europe": {
                "description": "Europe - Sentinel-5P Copernicus",
                "specializations": ["ESA Sentinel-5P", "Sensor.Community"],
                "indices": ["WHO Standards", "EU Air Quality Index"],
                "coverage": "Optimisé pour données Copernicus"
            },
            "South America": {
                "description": "Amérique du Sud - INPE/CPTEC",
                "specializations": ["INPE/CPTEC", "Sentinel-5P"],
                "indices": ["WHO Standards"],
                "coverage": "Focus Brésil et région"
            },
            "Global": {
                "description": "Couverture mondiale générale",
                "specializations": ["AIRS", "MERRA-2", "AQICN", "OpenAQ"],
                "indices": ["WHO Standards", "Generic AQI"],
                "coverage": "Toutes autres régions"
            }
        },
        "total_sources": 9,
        "cost": "0€ - 100% FREE",
        "note": "Tous les services utilisent uniquement des sources gratuites"
    }


@router.get("/sources")
async def get_data_sources():
    """Information sur toutes les sources de données utilisées"""
    return {
        "free_sources": {
            "nasa_official": {
                "TEMPO": "Satellite géostationnaire - Amérique du Nord",
                "AIRS": "Atmospheric Infrared Sounder - Mondial", 
                "MERRA-2": "Réanalyse atmosphérique moderne - Mondial"
            },
            "international_space": {
                "ESA Sentinel-5P": "Programme Copernicus - Union Européenne",
                "CSA OSIRIS": "Agence Spatiale Canadienne",
                "INPE/CPTEC": "Institut National Recherche Spatiale Brésil"
            },
            "global_networks": {
                "AQICN": "World Air Quality Index - 12,000+ stations (1000 req/jour gratuit)",
                "OpenAQ": "Plateforme open source qualité de l'air",
                "Sensor.Community": "Réseau citoyen européen"
            }
        },
        "standards_calculated": {
            "EPA_AQI": "United States Environmental Protection Agency Air Quality Index",
            "WHO_Guidelines": "World Health Organization Air Quality Guidelines 2021",
            "Canada_AQHI": "Air Quality Health Index - Environnement Canada"
        },
        "total_cost": "0€ - Complètement gratuit",
        "api_limits": "1000 requêtes/jour (AQICN), autres illimitées",
        "data_quality": "Sources scientifiques officielles de référence"
    }
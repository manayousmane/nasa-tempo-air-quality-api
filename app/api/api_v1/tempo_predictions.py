"""
🛰️ API PRÉDICTIONS TEMPO SIMPLIFIÉE
================================================================================
Endpoints pour prédictions air quality basées sur les modèles TEMPO
Utilise le TempoModelService pour les prédictions actuelles
================================================================================
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.services.tempo_model_service import TempoModelService

logger = logging.getLogger(__name__)

# Instance du service de modèles
tempo_service = TempoModelService()

router = APIRouter()

# ================================================================================
# MODÈLES PYDANTIC
# ================================================================================

class TempoCoordinates(BaseModel):
    """Coordonnées pour prédiction TEMPO"""
    latitude: float = Field(..., ge=40.0, le=70.0, description="Latitude (40°N-70°N)")
    longitude: float = Field(..., ge=-130.0, le=-70.0, description="Longitude (70°W-130°W)")

class TempoFeatures(BaseModel):
    """Features pour améliorer la prédiction"""
    hour: Optional[int] = Field(None, ge=0, le=23, description="Heure (0-23)")
    day_of_year: Optional[int] = Field(None, ge=1, le=365, description="Jour de l'année")
    temperature: Optional[float] = Field(None, description="Température (°C)")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidité (%)")
    pressure: Optional[float] = Field(None, description="Pression (hPa)")
    wind_speed: Optional[float] = Field(None, ge=0, description="Vitesse vent (m/s)")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Direction vent (°)")
    
    # Polluants actuels
    pm25_current: Optional[float] = Field(None, ge=0, description="PM2.5 actuel (µg/m³)")
    pm10_current: Optional[float] = Field(None, ge=0, description="PM10 actuel (µg/m³)")
    no2_current: Optional[float] = Field(None, ge=0, description="NO2 actuel (µg/m³)")
    o3_current: Optional[float] = Field(None, ge=0, description="O3 actuel (µg/m³)")
    co_current: Optional[float] = Field(None, ge=0, description="CO actuel (mg/m³)")
    so2_current: Optional[float] = Field(None, ge=0, description="SO2 actuel (µg/m³)")

class TempoPredictionRequest(BaseModel):
    """Requête de prédiction TEMPO"""
    coordinates: TempoCoordinates
    features: Optional[TempoFeatures] = None
    prediction_horizon_hours: Optional[int] = Field(1, ge=1, le=24, description="Horizon prédiction (heures)")

class TempoBatchRequest(BaseModel):
    """Requête batch pour plusieurs locations"""
    locations: List[TempoCoordinates] = Field(..., max_items=20, description="Max 20 locations")
    features: Optional[TempoFeatures] = None

class TempoPredictionResponse(BaseModel):
    """Réponse de prédiction TEMPO"""
    success: bool
    timestamp: datetime
    coordinates: TempoCoordinates
    predictions: Dict[str, Optional[float]]
    aqi: Optional[Dict[str, Any]]
    health_recommendations: Optional[Dict[str, str]]
    confidence: str
    error: Optional[str] = None

# ================================================================================
# ENDPOINTS API
# ================================================================================

@router.get("/coverage", response_model=Dict[str, Any])
async def get_tempo_coverage():
    """
    📍 Informations sur la zone de couverture TEMPO
    """
    return {
        "service": "NASA TEMPO Air Quality Predictions",
        "coverage_zone": {
            "name": "North America TEMPO Coverage",
            "latitude_range": {"min": 40.0, "max": 70.0},
            "longitude_range": {"min": -130.0, "max": -70.0},
            "countries": ["United States", "Canada"],
            "description": "TEMPO satellite coverage area over North America"
        },
        "capabilities": {
            "pollutants": ["PM2.5", "PM10", "NO2", "O3", "CO", "SO2"],
            "prediction_types": ["Single location", "Batch processing"],
            "max_batch_size": 20,
            "prediction_horizon": "1-24 hours"
        },
        "data_sources": {
            "satellite": "NASA TEMPO",
            "ml_models": "Specialized North America models",
            "training_data": "55,320 historical points"
        }
    }

@router.get("/models-status", response_model=Dict[str, Any])
async def get_models_status():
    """
    🤖 Status des modèles ML TEMPO
    """
    try:
        status = tempo_service.get_service_status()
        
        return {
            "service_status": "operational" if status["is_loaded"] else "degraded",
            "models_loaded": status["is_loaded"],
            "available_pollutants": status["pollutants"],
            "total_models": status["models_available"],
            "total_algorithms": status["total_algorithms"],
            "metadata_available": status["metadata_loaded"],
            "models_directory": status["models_directory"],
            "last_updated": status["last_updated"],
            "performance_note": "Models currently have low R² scores and are being improved",
            "version": "1.0-beta"
        }
        
    except Exception as e:
        logger.error(f"Erreur status modèles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur status modèles: {str(e)}")

@router.post("/predict", response_model=TempoPredictionResponse)
async def predict_air_quality(request: TempoPredictionRequest):
    """
    🎯 Prédiction air quality pour coordonnées spécifiques
    
    Prédit les concentrations de polluants pour une location donnée
    en Amérique du Nord (zone TEMPO).
    """
    try:
        if not tempo_service.is_loaded:
            raise HTTPException(
                status_code=503, 
                detail="Service modèles non disponible"
            )
        
        # Conversion des coordonnées
        coordinates = {
            "latitude": request.coordinates.latitude,
            "longitude": request.coordinates.longitude
        }
        
        # Conversion des features (avec valeurs par défaut)
        features_dict = {}
        if request.features:
            features_dict = request.features.dict(exclude_none=True)
        
        # Valeurs par défaut si pas spécifiées
        now = datetime.now()
        features_dict.setdefault("hour", now.hour)
        features_dict.setdefault("day_of_year", now.timetuple().tm_yday)
        
        # Prédictions pour tous les polluants
        predictions = tempo_service.predict_all_pollutants(coordinates, features_dict)
        
        # Calcul AQI
        aqi = tempo_service.calculate_aqi(predictions)
        
        # Recommandations santé
        health_recs = tempo_service.get_health_recommendations(aqi)
        
        return TempoPredictionResponse(
            success=True,
            timestamp=datetime.now(),
            coordinates=request.coordinates,
            predictions=predictions,
            aqi=aqi,
            health_recommendations=health_recs,
            confidence="low",  # Honnêteté sur la qualité actuelle
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur prédiction: {str(e)}")
        return TempoPredictionResponse(
            success=False,
            timestamp=datetime.now(),
            coordinates=request.coordinates,
            predictions={},
            aqi=None,
            health_recommendations=None,
            confidence="none",
            error=str(e)
        )

@router.post("/batch", response_model=Dict[str, Any])
async def predict_batch(request: TempoBatchRequest):
    """
    📊 Prédiction batch pour plusieurs locations
    
    Traite jusqu'à 20 locations simultanément.
    """
    try:
        if not tempo_service.is_loaded:
            raise HTTPException(
                status_code=503, 
                detail="Service modèles non disponible"
            )
        
        if len(request.locations) > 20:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 20 locations par batch"
            )
        
        # Features communes
        features_dict = {}
        if request.features:
            features_dict = request.features.dict(exclude_none=True)
        
        # Valeurs par défaut
        now = datetime.now()
        features_dict.setdefault("hour", now.hour)
        features_dict.setdefault("day_of_year", now.timetuple().tm_yday)
        
        # Traitement de chaque location
        results = []
        for i, coordinates in enumerate(request.locations):
            try:
                coord_dict = {
                    "latitude": coordinates.latitude,
                    "longitude": coordinates.longitude
                }
                
                predictions = tempo_service.predict_all_pollutants(coord_dict, features_dict)
                aqi = tempo_service.calculate_aqi(predictions)
                
                results.append({
                    "location_index": i,
                    "coordinates": coordinates.dict(),
                    "predictions": predictions,
                    "aqi": aqi,
                    "success": True,
                    "error": None
                })
                
            except Exception as e:
                results.append({
                    "location_index": i,
                    "coordinates": coordinates.dict(),
                    "predictions": {},
                    "aqi": None,
                    "success": False,
                    "error": str(e)
                })
        
        # Statistiques
        successful = sum(1 for r in results if r["success"])
        
        return {
            "batch_summary": {
                "total_locations": len(request.locations),
                "successful_predictions": successful,
                "failed_predictions": len(request.locations) - successful,
                "success_rate": successful / len(request.locations)
            },
            "predictions": results,
            "timestamp": datetime.now(),
            "confidence_note": "Current models have low accuracy and are being improved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur batch: {str(e)}")

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    ❤️ Vérification santé du service TEMPO
    """
    try:
        status = tempo_service.get_service_status()
        
        if status["is_loaded"]:
            return {
                "status": "healthy",
                "models": f"{status['models_available']} loaded",
                "pollutants": f"{len(status['pollutants'])} available",
                "note": "Service operational but model accuracy is low"
            }
        else:
            return {
                "status": "degraded",
                "models": "not loaded",
                "issue": "Model loading failed"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
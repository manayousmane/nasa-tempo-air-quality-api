"""
Modèles simplifiés pour l'API open source
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SimplePollutantMeasurement(BaseModel):
    """Mesure simple d'un polluant"""
    pollutant: str = Field(..., description="Nom du polluant (PM2.5, NO2, O3, etc.)")
    value: float = Field(..., description="Concentration mesurée")
    unit: str = Field(..., description="Unité de mesure (µg/m³, ppm, etc.)")
    confidence: float = Field(..., ge=0, le=1, description="Score de confiance")
    timestamp: datetime = Field(..., description="Timestamp de la mesure")


class SimpleLocation(BaseModel):
    """Location simplifiée"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class SimpleAirQualityResponse(BaseModel):
    """Réponse simplifiée pour qualité de l'air"""
    location: SimpleLocation
    timestamp: datetime
    measurements: List[SimplePollutantMeasurement]
    overall_aqi: int = Field(..., description="AQI global")
    air_quality_index: int = Field(..., description="Index qualité air")
    health_recommendation: str = Field(..., description="Recommandation santé")
    data_sources: List[str] = Field(default_factory=list, description="Sources de données")
    quality_score: float = Field(default=0.0, description="Score de qualité")
    region: str = Field(default="Unknown", description="Région")
    sources_active: int = Field(default=0, description="Nombre de sources actives")
    coverage_info: Dict[str, Any] = Field(default_factory=dict, description="Informations de couverture")
    data_sources: List[str] = Field(..., description="Sources de données utilisées")
    quality_score: float = Field(..., description="Score qualité global")
    region: str = Field(..., description="Région géographique")
    sources_active: int = Field(..., description="Nombre de sources actives")
    coverage_info: Dict[str, Any] = Field(..., description="Info couverture")


class SimpleForecastPrediction(BaseModel):
    """Prédiction simplifiée"""
    timestamp: datetime
    predicted_aqi: int
    confidence: float


class SimpleForecastResponse(BaseModel):
    """Réponse prévision simplifiée"""
    location: SimpleLocation
    forecast_timestamp: datetime
    predictions: List[SimpleForecastPrediction]
    model_info: Dict[str, Any]


class SimpleHistoricalResponse(BaseModel):
    """Réponse données historiques simplifiée"""
    location: SimpleLocation
    start_date: datetime
    end_date: datetime
    measurements: List[SimplePollutantMeasurement]
    summary: Dict[str, Any]
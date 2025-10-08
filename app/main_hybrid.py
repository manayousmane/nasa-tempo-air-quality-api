"""
🛰️ NASA TEMPO API - Service Hybride Intelligent
===============================================
V3.0 - Vraies données NASA TEMPO + OpenAQ + Fallback intelligent
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import math
from typing import List, Optional
import logging

# Import du service hybride intelligent
from app.services.intelligent_hybrid_service import hybrid_service

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NASA TEMPO Air Quality API - Hybrid Intelligence",
    description="🛰️ Vraies données NASA TEMPO + OpenAQ + Fallback intelligent basé sur patterns réels",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/location/full")
async def get_location_data(
    latitude: float = Query(..., description="Latitude de la localisation"),
    longitude: float = Query(..., description="Longitude de la localisation")
):
    """
    🛰️ Récupère les données de qualité de l'air - HYBRIDE INTELLIGENT
    
    Stratégie automatique:
    1. Essaie d'abord NASA TEMPO (si zone Amérique du Nord)
    2. Puis OpenAQ (données mondiales)
    3. Fallback intelligent avec patterns réels
    """
    try:
        logger.info(f"📍 Requesting data for {latitude}, {longitude}")
        
        # Utiliser le service hybride intelligent
        result = await hybrid_service.get_location_data(latitude, longitude)
        
        logger.info(f"✅ Data retrieved: {result.get('dataSource', 'Unknown source')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting location data: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/forecast")
async def get_forecast_data(
    latitude: float = Query(..., description="Latitude de la localisation"),
    longitude: float = Query(..., description="Longitude de la localisation"),
    hours: int = Query(24, description="Nombre d'heures de prédiction (1-72)", ge=1, le=72)
):
    """
    🔮 Prédictions de qualité de l'air - Modèles basés sur patterns NASA
    
    Utilise les données actuelles (vraies ou fallback intelligent) pour générer
    des prédictions basées sur les patterns observés par NASA TEMPO
    """
    try:
        logger.info(f"🔮 Forecast request for {latitude}, {longitude} - {hours}h")
        
        # Utiliser le service hybride intelligent
        result = await hybrid_service.get_forecast_data(latitude, longitude, hours)
        
        base_source = result.get('metadata', {}).get('base_data_source', 'Unknown')
        logger.info(f"✅ Forecast generated based on: {base_source}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/service/stats")
async def get_service_statistics():
    """
    📊 Statistiques du service hybride
    
    Montre l'utilisation des différentes sources de données:
    - NASA TEMPO (satellite)
    - OpenAQ (stations mondiales)  
    - Fallback intelligent
    """
    try:
        stats = hybrid_service.get_service_stats()
        return {
            "service_name": "NASA TEMPO Hybrid Intelligence",
            "version": "3.0.0",
            "status": "operational",
            "statistics": stats,
            "last_check": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/")
async def root():
    """
    🛰️ NASA TEMPO API - Service Hybride Intelligent
    """
    return {
        "service": "NASA TEMPO Air Quality API",
        "version": "3.0.0 - Hybrid Intelligence", 
        "description": "🛰️ Vraies données NASA TEMPO + OpenAQ + Fallback intelligent",
        "endpoints": {
            "/location/full": "Données actuelles (latitude, longitude)",
            "/forecast": "Prédictions qualité de l'air (latitude, longitude, hours)",
            "/service/stats": "Statistiques d'utilisation des sources de données"
        },
        "data_sources": [
            "NASA TEMPO (satellite data)",
            "OpenAQ (global network)",
            "Intelligent fallback (WHO/EPA patterns)"
        ],
        "coverage": "Mondial avec priorité Amérique du Nord (NASA TEMPO)",
        "status": "✅ Operational",
        "timestamp": datetime.now().isoformat() + "Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
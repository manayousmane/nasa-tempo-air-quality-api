"""
🌍 ENDPOINT LOCATION DATA SIMPLIFIÉ
================================================================================
Endpoint simple: nom → LocationDataType
================================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from app.services.location_geocoding_service import location_service
from app.services.tempo_model_service import TempoModelService

logger = logging.getLogger(__name__)

# Instance du service TEMPO
tempo_service = TempoModelService()

router = APIRouter()

# ================================================================================
# MODÈLE EXACT LocationDataType
# ================================================================================

class LocationDataType(BaseModel):
    """Structure exacte selon votre spécification"""
    name: str
    coordinates: List[float]  # [latitude, longitude]
    aqi: Optional[float] = None
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    windSpeed: Optional[float] = None
    windDirection: Optional[str] = None
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    lastUpdated: str

# ================================================================================
# ENDPOINT PRINCIPAL
# ================================================================================

@router.get("/location/{location_name}", response_model=LocationDataType)
async def get_location_data(location_name: str):
    """
    🎯 ENDPOINT PRINCIPAL: Nom → LocationDataType
    
    Entrée: Nom du pays, état, province ou ville
    Sortie: Données complètes au format LocationDataType
    
    Exemples:
    - GET /location/New York
    - GET /location/Toronto  
    - GET /location/California
    - GET /location/Ontario
    """
    try:
        # Géocodage de la location
        location_info = await location_service.geocode_location(location_name)
        
        if not location_info:
            raise HTTPException(
                status_code=404, 
                detail=f"Location '{location_name}' non trouvée. Locations supportées: États-Unis et Canada uniquement."
            )
        
        # Coordonnées
        lat = location_info["latitude"]
        lon = location_info["longitude"]
        coordinates = [lat, lon]
        
        # Prédictions air quality si disponibles
        aqi = None
        pm25 = pm10 = no2 = o3 = so2 = co = None
        
        if tempo_service.is_loaded and location_service.is_in_tempo_coverage(lat, lon):
            try:
                coord_dict = {"latitude": lat, "longitude": lon}
                features = {}  # Valeurs par défaut
                
                predictions = tempo_service.predict_all_pollutants(coord_dict, features)
                aqi_data = tempo_service.calculate_aqi(predictions)
                
                # Extraction des valeurs
                aqi = aqi_data.get("overall")
                pm25 = predictions.get("pm25")
                pm10 = predictions.get("pm10") 
                no2 = predictions.get("no2")
                o3 = predictions.get("o3")
                so2 = predictions.get("so2")
                co = predictions.get("co")
                
            except Exception as e:
                logger.warning(f"Erreur prédictions pour {location_name}: {str(e)}")
                # Continuer sans prédictions
        
        # Données météo par défaut (pourraient être enrichies avec vraie API météo)
        temperature = 15.0  # °C
        humidity = 65.0     # %
        windSpeed = 5.0     # m/s
        windDirection = "SW"
        pressure = 1013.25  # hPa
        visibility = 10.0   # km
        
        # Construction de la réponse LocationDataType
        return LocationDataType(
            name=location_info["name"],
            coordinates=coordinates,
            aqi=aqi,
            pm25=pm25,
            pm10=pm10,
            no2=no2,
            o3=o3,
            so2=so2,
            co=co,
            temperature=temperature,
            humidity=humidity,
            windSpeed=windSpeed,
            windDirection=windDirection,
            pressure=pressure,
            visibility=visibility,
            lastUpdated=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur endpoint location {location_name}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne lors de la récupération des données pour '{location_name}'"
        )

@router.get("/location", response_model=LocationDataType)
async def get_location_data_query(name: str = Query(..., description="Nom de la location")):
    """
    🎯 ENDPOINT ALTERNATIF avec query parameter
    
    Exemples:
    - GET /location?name=New York
    - GET /location?name=Toronto
    """
    return await get_location_data(name)

# ================================================================================
# ENDPOINTS UTILITAIRES
# ================================================================================

@router.get("/locations/available", response_model=List[str])
async def get_available_location_names():
    """
    📋 Liste des noms de locations disponibles
    """
    try:
        locations = location_service.get_all_available_locations()
        return [loc["name"] for loc in locations]
        
    except Exception as e:
        logger.error(f"Erreur liste locations: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur récupération liste locations")

@router.get("/locations/examples", response_model=List[LocationDataType])
async def get_location_examples():
    """
    📊 Exemples de données LocationDataType pour quelques villes
    """
    try:
        example_locations = ["New York", "Toronto", "Los Angeles", "Vancouver"]
        results = []
        
        for location_name in example_locations:
            try:
                location_data = await get_location_data(location_name)
                results.append(location_data)
            except:
                continue  # Ignorer les erreurs et continuer
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur exemples: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur génération exemples")
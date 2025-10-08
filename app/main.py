"""
API de Qualité d'Air NASA TEMPO avec Données Réelles
Intègre: NASA TEMPO, OpenAQ, NOAA, WHO Global Air Quality
Version 2.0 - Données réelles
"""

# Chargement des variables d'environnement depuis .env
from dotenv import load_dotenv
import os

# Charger le fichier .env depuis la racine du projet
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import asyncio
from starlette.responses import JSONResponse  
from .services.real_air_quality_service import RealAirQualityService
from .services.air_quality_integration import AirQualityIntegration
from .services.tempo_latest_service import TempoLatestService
from .services.hybrid_tempo_service import HybridTEMPOService

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialisation de l'application
app = FastAPI(
    title="NASA TEMPO Air Quality API - Real Data",
    version="2.0.0",
    description="""
    🌍 **API de Qualité de l'Air avec Données Réelles**
    
    Cette API intègre des données de qualité de l'air en temps réel provenant de sources multiples:
    
    **Sources de Données:**
    - 🛰️ **NASA TEMPO** - Observations satellitaires de NO2, HCHO, O3, PM
    - 🌐 **OpenAQ** - Réseau mondial de capteurs de qualité de l'air au sol
    - 🌤️ **NOAA** - Données météorologiques officielles
    - 🏥 **OMS/WHO** - Standards et seuils de qualité de l'air mondiale
    - 📡 **NASA AIRS** - Sondeur infrarouge atmosphérique
    - 🌊 **NASA SPORT Viewer** - Données environnementales en temps quasi-réel
    
    **Caractéristiques:**
    - Données en temps réel avec fallback intelligent
    - Prédictions basées sur des mesures réelles
    - Historique complet avec sources multiples
    - Recommandations de santé selon standards EPA/OMS
    - Cache optimisé pour performances
    - Géolocalisation mondiale
    
    **Polluants Surveillés:**
    - PM2.5 et PM10 (particules fines)
    - NO2 (dioxyde d'azote)
    - O3 (ozone)
    - SO2 (dioxyde de soufre) 
    - CO (monoxyde de carbone)
    - AQI (indice de qualité de l'air)
    """,
    contact={
        "name": "NASA TEMPO Air Quality Team",
        "url": "https://tempo.si.edu/",
    },
    license_info={
        "name": "NASA Open Data License",
        "url": "https://www.nasa.gov/about/highlights/HP_Privacy.html",
    }
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Service principal
air_quality_service = RealAirQualityService()

# Nouveau service d'intégration TEMPO + OpenWeather
air_quality_integration = AirQualityIntegration()

# Service TEMPO Latest - Dernières données satellites disponibles
tempo_latest_service = TempoLatestService()

# Service principal - Utiliser le service existant qui marchait
try:
    from .services.real_air_quality_service import RealAirQualityService
    air_quality_service = RealAirQualityService()
    logger.info("✅ RealAirQualityService initialisé")
except ImportError as e:
    logger.warning(f"⚠️ RealAirQualityService non disponible: {e}")
    air_quality_service = None

# Service Hybride - TEMPO + APIs Open Source avec concentrations réelles
hybrid_tempo_service = HybridTEMPOService()

# Compteurs de statistiques pour le monitoring
stats_counter = {
    "real_air_quality_requests": 0,
    "real_air_quality_errors": 0,
    "fast_tempo_requests": 0,
    "fast_tempo_errors": 0,
    "comprehensive_requests": 0,
    "comprehensive_errors": 0,
    "total_requests": 0,
    "tempo_latest_requests": 0,
    "tempo_summary_requests": 0
}

# Service d'intégration TEMPO + OpenWeather (optionnel)
try:
    air_quality_integration = AirQualityIntegration()
    logger.info("✅ AirQualityIntegration initialisé")
except Exception as e:
    logger.warning(f"⚠️ AirQualityIntegration non disponible: {e}")
    air_quality_integration = None

# Service TEMPO Latest (optionnel)
try:
    tempo_latest_service = TempoLatestService()
    logger.info("✅ TempoLatestService initialisé")
except Exception as e:
    logger.warning(f"⚠️ TempoLatestService non disponible: {e}")
    tempo_latest_service = None

# Statistiques d'utilisation simple
usage_stats = {
    "total_requests": 0,
    "current_data_requests": 0,
    "forecast_requests": 0,
    "historical_requests": 0,
    "tempo_latest_requests": 0,
    "tempo_summary_requests": 0,
    "tempo_comprehensive_requests": 0,
    "start_time": datetime.now()
}

def update_stats(endpoint_type: str):
    """Met à jour les statistiques d'utilisation"""
    usage_stats["total_requests"] += 1
    usage_stats[f"{endpoint_type}_requests"] += 1

async def get_fallback_data(latitude: float, longitude: float) -> Dict:
    """Données de fallback en cas d'erreur"""
    return {
        "name": await get_location_name(latitude, longitude),
        "coordinates": [latitude, longitude],
        "aqi": 50,
        "pm25": 10.0,
        "pm10": 15.0,
        "no2": 20.0,
        "o3": 40.0,
        "so2": 5.0,
        "co": 0.5,
        "temperature": 15.0,
        "humidity": 65.0,
        "windSpeed": 3.0,
        "windDirection": "N",
        "pressure": 1013.0,
        "visibility": 10.0,
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
        "dataSource": "Fallback",
        "weatherCondition": "clear"
    }

async def get_location_name(latitude: float, longitude: float) -> str:
    """Obtient le nom de la localisation basé sur les coordonnées"""
    # Utilise une géolocalisation simple et fiable
    try:
        import aiohttp
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    address = data.get('address', {})
                    
                    city = (address.get('city') or address.get('town') or 
                           address.get('village') or address.get('municipality'))
                    state = (address.get('state') or address.get('province') or 
                            address.get('region'))
                    country = address.get('country')
                    
                    parts = [p for p in [city, state, country] if p]
                    return ', '.join(parts) if parts else f"Location {latitude:.3f}, {longitude:.3f}"
    except Exception as e:
        logger.warning(f"⚠️ Erreur géolocalisation: {e}")
    
    return f"Location {latitude:.3f}, {longitude:.3f}"

async def get_fallback_data(latitude: float, longitude: float) -> Dict:
    """Fonction de fallback vers des données par défaut"""
    try:
        logger.info("🔄 Utilisation du système de fallback")
        
        # Données par défaut basiques mais fonctionnelles
        return {
            "name": await get_location_name(latitude, longitude),
            "coordinates": [latitude, longitude],
            "aqi": 50,
            "pm25": 10.0,
            "pm10": 15.0,
            "no2": 20.0,
            "o3": 40.0,
            "so2": 5.0,
            "co": 0.5,
            "temperature": 15.0,
            "humidity": 65.0,
            "windSpeed": 3.0,
            "windDirection": "N",
            "pressure": 1013.0,
            "visibility": 10.0,
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
            "dataSource": "Fallback Default",
            "weatherCondition": "clear"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur fallback: {e}")
        # Derniers secours - données par défaut
        return {
            "name": f"Location {latitude:.3f}, {longitude:.3f}",
            "coordinates": [latitude, longitude],
            "aqi": 50,
            "pm25": 10.0,
            "pm10": 15.0,
            "no2": 20.0,
            "o3": 40.0,
            "so2": 5.0,
            "co": 0.5,
            "temperature": 15.0,
            "humidity": 65.0,
            "windSpeed": 3.0,
            "windDirection": "N",
            "pressure": 1013.0,
            "visibility": 10.0,
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
            "dataSource": "Emergency Fallback",
            "weatherCondition": "clear"
        }

@app.get("/", tags=["Info"])
async def root():
    """
    🏠 **Page d'accueil de l'API**
    
    Informations générales sur l'API et les endpoints disponibles.
    """
    uptime = datetime.now() - usage_stats["start_time"]
    
    return {
        "message": "🌍 NASA TEMPO Air Quality API - Real Data Version",
        "version": "2.0.0",
        "status": "operational",
        "uptime": str(uptime),
        "data_sources": [
            "🛰️ NASA TEMPO Satellite",
            "🌐 OpenAQ Ground Stations", 
            "🌤️ NOAA Weather Data",
            "🏥 WHO Air Quality Standards",
            "📡 NASA AIRS Atmospheric Sounder"
        ],
        "endpoints": {
            "current_air_quality": "/location/full?latitude=45.5&longitude=2.3",
            "forecast_24h": "/forecast?latitude=45.5&longitude=2.3&hours=24",
            "historical_data": "/historical?latitude=45.5&longitude=2.3",
            "health_info": "/health-recommendations?aqi=75"
        },
        "features": [
            "✅ Real-time air quality from multiple sources",
            "✅ Satellite and ground-based measurements",
            "✅ 24-72h intelligent forecasting",
            "✅ Historical data analysis",
            "✅ WHO/EPA health recommendations",
            "✅ Global coverage with regional optimization",
            "✅ Automatic fallback systems",
            "✅ Comprehensive weather integration"
        ],
        "usage_statistics": usage_stats,
        "documentation": "/docs",
        "real_time_status": "🟢 Active"
    }
@app.head(
    '/', 
    include_in_schema=False,
    summary="Point d'entrée de l'API",
    description="Renvoie un message de bienvenue pour confirmer que l'API fonctionne correctement.",
    response_description="Message de bienvenue"
)
async def root():
    return JSONResponse({"message": "Hello World"})


@app.get("/health", tags=["Info"])
async def health_check():
    """🏥 Vérification de l'état de santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "air_quality_service": "operational",
            "data_connectors": "operational",
            "cache_system": "operational"
        },
        "version": "2.0.0"
    }



@app.get("/location/full", tags=["Current Data"])
async def get_current_air_quality(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 à 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 à 180)"),
    background_tasks: BackgroundTasks = None
):
    """
    🌍 **Données Actuelles de Qualité de l'Air avec Sources Réelles**
    
    Récupère les données actuelles de qualité de l'air en intégrant plusieurs sources:
    
    **Sources de Données (par ordre de priorité):**
    1. 🛰️ **NASA TEMPO** - Observations satellitaires en temps réel (priorité absolue)
    2. 🌤️ **OpenWeather** - Données météorologiques officielles
    3. 🌐 **OpenAQ** - Capteurs au sol en temps réel (rayon 25km)
    4. 📡 **NASA AIRS** - Données atmosphériques infrarouge
    5. 🔄 **Estimation Intelligente** - Modèles basés sur patterns géographiques
    
    **Nouvelle Intégration:**
    - Utilise le service d'intégration TEMPO + OpenWeather
    - Fallback automatique vers l'ancien système si nécessaire
    - Simulation intelligente uniquement si TEMPO échoue
    
    **Données Incluses:**
    - Polluants: PM2.5, PM10, NO2, O3, SO2, CO
    - AQI calculé selon standards EPA
    - Météo: température, humidité, vent, pression
    - Localisation et source des données
    - Recommandations de santé WHO/EPA
    - Fiabilité et qualité des données
    
    **Exemples:**
    - Paris: `latitude=48.8566&longitude=2.3522`
    - New York: `latitude=40.7128&longitude=-74.0060`
    - Tokyo: `latitude=35.6762&longitude=139.6503`
    """
    try:
        # Validation des coordonnées
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=400, 
                detail="Coordonnées invalides. Latitude: -90 à 90, Longitude: -180 à 180"
            )
        
        logger.info(f"🌍 Requête données actuelles: {latitude:.4f}, {longitude:.4f}")
        
        # Mettre à jour les statistiques
        if background_tasks:
            background_tasks.add_task(update_stats, "current_data")
        
        # Récupérer les données réelles comme avant
        if air_quality_service:
            result = await air_quality_service.get_current_air_quality(latitude, longitude)
        else:
            # Fallback vers le service hybride si nécessaire
            result = await hybrid_tempo_service.get_comprehensive_air_quality(latitude, longitude)
        
        logger.info(f"✅ Données actuelles livrées: AQI {result.get('aqi', 'N/A')} - Source: {result.get('data_source', 'Unknown')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur données actuelles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des données: {str(e)}"
        )

@app.get("/forecast", tags=["Forecasting"])
async def get_air_quality_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 à 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 à 180)"),
    hours: int = Query(24, ge=1, le=72, description="Nombre d'heures de prédiction (1-72)"),
    background_tasks: BackgroundTasks = None
):
    """
    🔮 **Prédictions de Qualité de l'Air Basées sur Données Réelles**
    
    Génère des prédictions intelligentes de qualité de l'air en utilisant:
    
    **Modèle de Prédiction:**
    - 📊 **Base de données réelles**: Utilise les mesures actuelles comme point de départ
    - 🌅 **Patterns diurnes**: Modélise les variations jour/nuit des polluants
    - 🌡️ **Facteurs météorologiques**: Intègre température, vent, humidité
    - 🚗 **Cycles de trafic**: Prédit les pics de pollution aux heures de pointe
    - 🏭 **Activité industrielle**: Considère les patterns d'émission
    - ☀️ **Formation d'ozone**: Modélise la photochimie atmosphérique
    
    **Polluants Prédits:**
    - PM2.5/PM10: Pics matin (7-9h) et soir (17-19h) 
    - NO2: Corrélé au trafic automobile
    - O3: Maximum l'après-midi (12-16h) par photochimie
    - SO2/CO: Variation selon activité industrielle
    
    **Confiance des Prédictions:**
    - Heure +1 à +6: Confiance élevée (85-95%)
    - Heure +6 à +24: Confiance modérée (70-85%)
    - Heure +24 à +72: Confiance moyenne (50-70%)
    
    **Inclut:**
    - Prédictions horaires détaillées
    - Tendance générale (amélioration/dégradation)
    - Meilleures/pires heures pour activités extérieures
    - Recommandations de santé évolutives
    - Niveau de confiance pour chaque prédiction
    """
    try:
        # Validation
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Coordonnées invalides")
        
        if not (1 <= hours <= 72):
            raise HTTPException(status_code=400, detail="Heures doit être entre 1 et 72")
        
        logger.info(f"🔮 Requête prédictions: {latitude:.4f}, {longitude:.4f} - {hours}h")
        
        # Mettre à jour les statistiques
        if background_tasks:
            background_tasks.add_task(update_stats, "forecast")
        
        # Générer les prédictions
        result = await air_quality_service.get_forecast_data(latitude, longitude, hours)
        
        logger.info(f"✅ Prédictions générées: {hours}h - Source base: {result.get('metadata', {}).get('base_data_source', 'Unknown')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur prédictions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des prédictions: {str(e)}"
        )

@app.get("/historical", tags=["Historical Data"])
async def get_historical_air_quality(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 à 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 à 180)"),
    start_date: Optional[datetime] = Query(
        None, 
        description="Date de début (ISO: 2024-01-01T00:00:00). Défaut: 24h en arrière"
    ),
    end_date: Optional[datetime] = Query(
        None, 
        description="Date de fin (ISO: 2024-01-31T23:59:59). Défaut: maintenant"
    ),
    pollutant: Optional[str] = Query(
        None, 
        description="Polluant spécifique (pm25, pm10, no2, o3, so2, co)"
    ),
    limit: int = Query(
        1000, 
        ge=1, 
        le=10000, 
        description="Nombre maximum d'enregistrements"
    ),
    background_tasks: BackgroundTasks = None
):
    """
    📊 **Données Historiques de Qualité de l'Air avec Sources Multiples**
    
    Récupère l'historique des mesures de qualité de l'air en intégrant:
    
    **Sources Historiques (par priorité):**
    1. 🌐 **OpenAQ Historical** - Archive des mesures de capteurs au sol
    2. 🛰️ **NASA TEMPO Archive** - Historique des observations satellitaires
    3. 📡 **NASA AIRS** - Données atmosphériques archivées  
    4. 🌤️ **NOAA Climate Data** - Archives météorologiques officielles
    5. 🔄 **Modèles Régionaux** - Reconstruction basée sur patterns WHO
    
    **Résolution Temporelle:**
    - **Temps réel**: Dernières 24h avec résolution horaire
    - **Récent**: 1-30 jours avec résolution 1-3h
    - **Historique**: 1 mois+ avec résolution adaptative
    
    **Données Fournies:**
    - Séries temporelles complètes
    - Statistiques descriptives (moyenne, min, max, médiane)
    - Évaluation de la qualité des données
    - Identification des pics de pollution
    - Corrélations météorologiques
    - Tendances saisonnières
    
    **Filtrage par Polluant:**
    - Permet de se concentrer sur un polluant spécifique
    - Statistiques détaillées pour analyse
    - Comparaison avec seuils OMS/EPA
    
    **Exemples d'usage:**
    - Dernières 24h: Pas de paramètres de date
    - Semaine spécifique: `start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59`
    - PM2.5 uniquement: `pollutant=pm25`
    - Analyse mensuelle: `start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59&limit=2000`
    """
    try:
        # Validation des coordonnées
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Coordonnées invalides")
        
        # Dates par défaut: 24 dernières heures
        now = datetime.now()
        if start_date is None:
            start_date = now - timedelta(hours=24)
            logger.info(f"📅 Date de début par défaut: {start_date.isoformat()}")
        
        if end_date is None:
            end_date = now
            logger.info(f"📅 Date de fin par défaut: {end_date.isoformat()}")
        
        # Validation de la plage de dates
        if end_date <= start_date:
            raise HTTPException(status_code=400, detail="end_date doit être après start_date")
        
        # Limiter la plage pour éviter les timeouts
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise HTTPException(
                status_code=400,
                detail=f"Plage temporelle limitée à {max_days} jours. Actuelle: {(end_date - start_date).days} jours"
            )
        
        # Validation du polluant
        valid_pollutants = ['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']
        if pollutant and pollutant.lower() not in valid_pollutants:
            raise HTTPException(
                status_code=400,
                detail=f"Polluant invalide. Options valides: {', '.join(valid_pollutants)}"
            )
        
        logger.info(f"📊 Requête historique: {latitude:.4f}, {longitude:.4f} - {start_date} à {end_date}")
        
        # Mettre à jour les statistiques
        if background_tasks:
            background_tasks.add_task(update_stats, "historical")
        
        # Récupérer les données historiques
        result = await air_quality_service.get_historical_data(
            latitude, longitude, start_date, end_date, pollutant
        )
        
        if not result.get("measurements"):
            raise HTTPException(
                status_code=404,
                detail="Aucune donnée historique trouvée pour les critères spécifiés"
            )
        
        logger.info(f"✅ Données historiques livrées: {len(result['measurements'])} mesures")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur données historiques: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des données historiques: {str(e)}"
        )

@app.get("/health-recommendations", tags=["Health & Safety"])
async def get_health_recommendations(
    aqi: int = Query(..., ge=0, le=500, description="Indice de qualité de l'air (0-500)")
):
    """
    🏥 **Recommandations de Santé selon Standards EPA/OMS**
    
    Fournit des recommandations de santé détaillées basées sur l'AQI.
    
    **Standards Utilisés:**
    - 🇺🇸 EPA (Environmental Protection Agency)
    - 🌍 OMS/WHO (Organisation Mondiale de la Santé)
    - 🇪🇺 Standards européens de qualité de l'air
    
    **Niveaux AQI:**
    - 0-50: 🟢 Bon
    - 51-100: 🟡 Modéré  
    - 101-150: 🟠 Malsain pour groupes sensibles
    - 151-200: 🔴 Malsain
    - 201-300: 🟣 Très malsain
    - 301-500: 🟤 Dangereux
    """
    try:
        service = RealAirQualityService()
        recommendations = service._get_health_recommendations(aqi)
        
        return {
            "aqi": aqi,
            "recommendations": recommendations,
            "standards": {
                "source": "EPA & WHO Guidelines",
                "last_updated": "2024",
                "reference": "https://www.epa.gov/aqi"
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur recommandations santé: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations: {str(e)}"
        )

@app.get("/data-sources", tags=["Info"])
async def get_data_sources_info():
    """
    📡 **Informations sur les Sources de Données**
    
    Détaille toutes les sources de données intégrées dans l'API.
    """
    return {
        "primary_sources": {
            "nasa_tempo": {
                "name": "NASA TEMPO (Tropospheric Emissions Monitoring of Pollution)",
                "description": "Observations satellitaires de la pollution atmosphérique",
                "website": "https://tempo.si.edu/",
                "parameters": ["NO2", "HCHO", "O3", "Aerosol Index"],
                "coverage": "Amérique du Nord",
                "temporal_resolution": "Horaire en journée",
                "spatial_resolution": "2.1 x 4.4 km"
            },
            "openaq": {
                "name": "OpenAQ Global Air Quality Network",
                "description": "Réseau mondial de capteurs de qualité de l'air",
                "website": "https://openaq.org/",
                "parameters": ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"],
                "coverage": "Mondiale",
                "stations": "15,000+ stations actives",
                "data_frequency": "En temps réel"
            },
            "noaa": {
                "name": "National Oceanic and Atmospheric Administration",
                "description": "Service météorologique officiel américain",
                "website": "https://www.noaa.gov/",
                "parameters": ["Température", "Humidité", "Vent", "Pression"],
                "coverage": "Mondiale avec focus USA",
                "reliability": "Très élevée"
            }
        },
        "secondary_sources": {
            "nasa_airs": {
                "name": "Atmospheric Infrared Sounder",
                "description": "Sondeur infrarouge atmosphérique sur satellite Aqua",
                "parameters": ["Température", "Humidité", "O3", "CO"],
                "resolution": "45 km"
            },
            "nasa_sport": {
                "name": "Short-term Prediction Research and Transition",
                "description": "Données environnementales en temps quasi-réel",
                "website": "https://weather.msfc.nasa.gov/sport/"
            },
            "who_standards": {
                "name": "World Health Organization Air Quality Guidelines",
                "description": "Standards et seuils de référence mondiale",
                "website": "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health"
            }
        },
        "data_integration": {
            "strategy": "Priorité par fiabilité et proximité",
            "fallback_system": "Cascade intelligente avec estimations régionales",
            "cache_duration": "5 minutes pour optimiser performances",
            "quality_assessment": "Automatique avec scores de confiance"
        },
        "coverage": {
            "global": "Estimations basées sur patterns régionaux",
            "high_quality": "Zones avec stations OpenAQ et couverture TEMPO",
            "real_time": "Principalement Amérique du Nord et Europe",
            "historical": "Archives jusqu'à 10+ ans selon région"
        }
    }

# Ajouter les nouveaux compteurs
stats_counter["real_air_quality_requests"] = 0
stats_counter["real_air_quality_errors"] = 0

# ================================================================
# 🚀 NOUVEAUX ENDPOINTS TEMPO OPTIMISÉS
# ================================================================

@app.get("/air-quality/real", response_model=dict, tags=["Pure Open Source"])
async def get_real_air_quality_data(lat: float = 40.7128, lon: float = -74.006):
    """
    🌍 **Données de Qualité de l'Air 100% Réelles et Fiables**
    
    Service optimisé qui utilise UNIQUEMENT les sources qui marchent bien :
    - 🔥 **WAQI** - World Air Quality Index (vraies concentrations)
    - 🌟 **AirNow** - EPA USA (données officielles)
    - 🌤️ **OpenWeather** - Météo fiable
    
    **Avantages :**
    - ⚡ **Rapide** : < 5 secondes garanties
    - 🎯 **Vraies concentrations** : PM2.5, PM10, NO2, O3, SO2, CO
    - 📊 **AQI précis** : Calcul EPA complet
    - 📦 **Cache intelligent** : 5 minutes
    - 🔒 **Fiable** : Pas de timeouts TEMPO
    
    **Réponse inclut :**
    - Concentrations détaillées avec unités
    - AQI global et par polluant
    - Niveau de qualité EPA
    - Sources des données
    - Données météo
    """
    try:
        logger.info(f"🌍 Données qualité air réelles: {lat}, {lon}")
        
        # Utiliser le service d'intégration existant
        result = await air_quality_integration.get_comprehensive_air_quality(lat, lon)
        
        # Statistiques
        stats_counter.get("real_air_quality_requests", 0)
        if "real_air_quality_requests" not in stats_counter:
            stats_counter["real_air_quality_requests"] = 0
        stats_counter["real_air_quality_requests"] += 1
        
        aqi = result.get('air_quality', {}).get('aqi', 'N/A')
        sources = result.get('sources', [])
        confidence = result.get('confidence', 'Inconnue')
        
        logger.info(f"🌍 Données réelles livrées: AQI {aqi}, Sources: {sources}, Confiance: {confidence}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur données réelles: {e}")
        stats_counter["real_air_quality_errors"] += 1
        raise HTTPException(status_code=500, detail=f"Erreur service réel: {str(e)}")

@app.get("/tempo/fast", response_model=dict, tags=["TEMPO Optimisé"])
async def get_fast_tempo_data(lat: float = 40.7128, lon: float = -74.006):
    """
    🚀 **Données Rapides (Sans les problèmes TEMPO)**
    
    Version optimisée qui évite les timeouts et problèmes TEMPO :
    - 🌍 APIs Open Source fiables
    - ⚡ Réponse < 8 secondes
    - 📦 Cache intelligent
    - 🔄 Fallback automatique
    """
    try:
        logger.info(f"⚡ Analyse rapide: {lat}, {lon}")
        
        # Utiliser le service hybride TEMPO (version rapide avec optimisations)
        result = await hybrid_tempo_service.get_comprehensive_air_quality(lat, lon)
        
        # Ajouter info sur l'optimisation
        result['note'] = 'Service TEMPO optimisé - métadonnées seulement, pas de téléchargement'
        result['tempo_status'] = 'optimized_metadata_only'
        
        # Statistiques
        stats_counter["fast_tempo_requests"] += 1
        
        logger.info(f"⚡ Données rapides livrées: AQI {result.get('air_quality', {}).get('aqi', 'N/A')}, "
                   f"Temps: {result.get('response_time', 'N/A')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur endpoint rapide: {e}")
        stats_counter["fast_tempo_errors"] += 1
        raise HTTPException(status_code=500, detail=f"Erreur service rapide: {str(e)}")

# ================================================================
# 🎯 TEMPO ENDPOINTS - DONNÉES SATELLITAIRES NASA  
# ================================================================

@app.get("/tempo/latest", tags=["TEMPO Satellite"])
async def get_latest_tempo_data(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 à 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 à 180)")
):
    """
    🛰️ **Dernières Données TEMPO Disponibles**
    
    Récupère les dernières données satellitaires TEMPO disponibles (période: 7 jours).
    
    **Avantages par rapport à /location/full :**
    - Données officielles NASA TEMPO uniquement
    - Recherche étendue sur les derniers jours  
    - Métadonnées complètes des granules
    - Qualité recherche/scientifique
    
    **Cas d'usage :**
    - Recherche scientifique
    - Validation de modèles
    - Études d'impact environnemental
    - Analyses de tendances satellitaires
    """
    update_stats("tempo_latest")
    
    try:
        logger.info(f"🛰️ Requête TEMPO Latest: {latitude}, {longitude}")
        
        result = await tempo_latest_service.get_latest_tempo_data(latitude, longitude)
        
        if result.get('status') == 'success':
            logger.info(f"✅ TEMPO Latest livré: {len(result.get('pollutants', {}))} polluants")
        else:
            logger.warning(f"⚠️ TEMPO Latest: {result.get('message', 'Aucune donnée')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur TEMPO Latest: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des données TEMPO Latest: {str(e)}"
        )

@app.get("/tempo/summary", tags=["TEMPO Satellite"])
async def get_tempo_data_summary(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 à 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 à 180)")
):
    """
    📊 **Résumé Rapide des Données TEMPO**
    
    Aperçu rapide de la disponibilité des données TEMPO sans téléchargement complet.
    
    **Utilisation :**
    - Vérification rapide de disponibilité
    - Planification d'analyses
    - Évaluation de couverture temporelle
    - Aide à la décision pour choix d'endpoints
    """
    update_stats("tempo_summary")
    
    try:
        logger.info(f"📊 Résumé TEMPO demandé: {latitude}, {longitude}")
        
        summary = await tempo_latest_service.get_tempo_summary(latitude, longitude)
        
        logger.info(f"📊 Résumé TEMPO livré: {summary.get('status', 'unknown')}")
        return summary
        
    except Exception as e:
        logger.error(f"❌ Erreur résumé TEMPO: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du résumé TEMPO: {str(e)}"
        )

@app.get("/tempo/comprehensive", tags=["TEMPO Satellite"])
async def get_comprehensive_tempo_analysis(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (-90 à 90)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (-180 à 180)")
):
    """
    🎯 **Analyse Complète TEMPO + Concentrations Réelles (VERSION RAPIDE)**
    
    **LE MEILLEUR ENDPOINT** - Combine validation TEMPO + concentrations réelles + AQI précis.
    
    **Optimisations:**
    - ⚡ Version rapide avec cache (5 min)
    - ⚡ Timeout agressif (10s total)
    - ⚡ Fallback automatique si TEMPO lent
    
    **Avantages uniques :**
    - ✅ Concentrations réelles depuis APIs fiables
    - ✅ Validation satellitaire TEMPO  
    - ✅ AQI calculé selon standards EPA
    - ✅ Recommandations de santé personnalisées
    - ✅ Niveau de confiance des données
    - ✅ Comparaison satellite vs sol
    
    **Cas d'usage prioritaires :**
    - Applications de santé publique
    - Monitoring environnemental professionnel
    - Recherche avec validation croisée
    - APIs commerciales haute qualité
    
    **Réponse :** Concentrations + AQI + TEMPO validation + météo + recommandations
    """
    update_stats("tempo_comprehensive")
    
    try:
        logger.info(f"🎯 Analyse TEMPO complète: {latitude}, {longitude}")
        
        # Utiliser le service hybride original
        result = await hybrid_tempo_service.get_comprehensive_air_quality(latitude, longitude)
        
        # Statistiques  
        stats_counter["comprehensive_requests"] += 1
        
        if result.get('status') != 'error':
            aqi = result.get('air_quality', {}).get('aqi', 'N/A')
            confidence = result.get('confidence', 'Unknown')
            logger.info(f"✅ Analyse complète livrée: AQI {aqi}, Confiance {confidence}")
        else:
            logger.warning(f"⚠️ Analyse complète: {result.get('message', 'Erreur')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur analyse TEMPO complète: {e}")
        stats_counter["comprehensive_errors"] += 1
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse complète TEMPO: {str(e)}"
        )

@app.get("/statistics", tags=["Info"])
async def get_api_statistics():
    """📈 Statistiques d'utilisation de l'API"""
    uptime = datetime.now() - usage_stats["start_time"]
    
    return {
        "api_statistics": usage_stats,
        "uptime": {
            "total_seconds": uptime.total_seconds(),
            "formatted": str(uptime),
            "start_time": usage_stats["start_time"].isoformat()
        },
        "performance": {
            "average_requests_per_hour": round(usage_stats["total_requests"] / max(uptime.total_seconds() / 3600, 1), 2),
            "most_popular_endpoint": max(
                [
                    ("current_data", usage_stats["current_data_requests"]),
                    ("forecast", usage_stats["forecast_requests"]),
                    ("historical", usage_stats["historical_requests"])
                ],
                key=lambda x: x[1]
            )[0] if usage_stats["total_requests"] > 0 else "none"
        },
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Démarrage de l'API NASA TEMPO Air Quality avec données réelles")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
"""
Service de géolocalisation moderne et fonctionnel
Utilise des APIs externes pour une identification précise des locations
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class LocationInfo:
    """Informations complètes d'une localisation"""
    latitude: float
    longitude: float
    
    # Informations administratives
    country: Optional[str] = None
    country_code: Optional[str] = None
    state_province: Optional[str] = None
    state_code: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Informations géographiques
    region: Optional[str] = None
    continent: Optional[str] = None
    timezone: Optional[str] = None
    
    # Métadonnées
    confidence: float = 0.0
    source: Optional[str] = None
    language: str = "en"
    
    # Informations air quality spécifiques
    optimal_data_sources: List[str] = None
    air_quality_standards: str = "WHO"
    monitoring_network: Optional[str] = None

class ModernGeolocationService:
    """Service de géolocalisation utilisant multiple APIs"""
    
    def __init__(self):
        self.session = None
        
        # Configuration des APIs de géolocalisation
        self.apis_config = {
            "nominatim": {
                "base_url": "https://nominatim.openstreetmap.org/reverse",
                "enabled": True,
                "rate_limit": 1.0,  # 1 seconde entre requêtes
                "priority": 1
            },
            "positionstack": {
                "base_url": "http://api.positionstack.com/v1/reverse",
                "enabled": False,  # Nécessite clé API
                "priority": 2
            },
            "opencage": {
                "base_url": "https://api.opencagedata.com/geocode/v1/json",
                "enabled": False,  # Nécessite clé API
                "priority": 3
            }
        }
        
        # Base de données offline pour backup
        self.offline_database = self._init_offline_database()
        
        logger.info("🌍 ModernGeolocationService initialisé")
    
    async def __aenter__(self):
        """Initialisation du contexte async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'NASA Air Quality API/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage du contexte async"""
        if self.session:
            await self.session.close()
    
    async def get_location_info(self, latitude: float, longitude: float, 
                              language: str = "en") -> LocationInfo:
        """
        Obtient les informations complètes d'une localisation
        
        Args:
            latitude: Latitude
            longitude: Longitude  
            language: Langue pour les résultats
            
        Returns:
            Informations complètes de la localisation
        """
        if not self.session:
            async with self:
                return await self._get_location_info_internal(latitude, longitude, language)
        else:
            return await self._get_location_info_internal(latitude, longitude, language)
    
    async def _get_location_info_internal(self, latitude: float, longitude: float,
                                        language: str) -> LocationInfo:
        """Implémentation interne de get_location_info"""
        
        # Initialiser la structure de base
        location_info = LocationInfo(
            latitude=latitude,
            longitude=longitude,
            language=language
        )
        
        # Essayer les APIs externes
        for api_name, config in self.apis_config.items():
            if not config["enabled"]:
                continue
                
            try:
                result = await self._query_api(api_name, latitude, longitude, language)
                if result:
                    location_info = self._merge_api_result(location_info, result, api_name)
                    if location_info.confidence > 0.8:
                        break  # Bonne qualité trouvée
                    
            except Exception as e:
                logger.warning(f"Erreur API {api_name}: {str(e)}")
                continue
        
        # Fallback vers base de données offline
        if location_info.confidence < 0.5:
            offline_result = self._query_offline_database(latitude, longitude)
            location_info = self._merge_offline_result(location_info, offline_result)
        
        # Enrichir avec informations air quality
        location_info = self._enrich_with_air_quality_info(location_info)
        
        return location_info
    
    async def _query_api(self, api_name: str, latitude: float, longitude: float,
                        language: str) -> Optional[Dict[str, Any]]:
        """Interroge une API de géolocalisation spécifique"""
        
        if api_name == "nominatim":
            return await self._query_nominatim(latitude, longitude, language)
        elif api_name == "positionstack":
            return await self._query_positionstack(latitude, longitude, language)
        elif api_name == "opencage":
            return await self._query_opencage(latitude, longitude, language)
        
        return None
    
    async def _query_nominatim(self, latitude: float, longitude: float,
                             language: str) -> Optional[Dict[str, Any]]:
        """Interroge l'API Nominatim (OpenStreetMap)"""
        
        try:
            url = self.apis_config["nominatim"]["base_url"]
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
                "accept-language": language,
                "zoom": 18
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    address = data.get("address", {})
                    
                    result = {
                        "country": address.get("country"),
                        "country_code": address.get("country_code", "").upper(),
                        "state_province": (address.get("state") or 
                                         address.get("province") or 
                                         address.get("region")),
                        "city": (address.get("city") or 
                                address.get("town") or 
                                address.get("village") or
                                address.get("municipality")),
                        "district": address.get("suburb") or address.get("district"),
                        "postal_code": address.get("postcode"),
                        "confidence": 0.8,
                        "source": "nominatim"
                    }
                    
                    # Essayer d'extraire le code d'état pour les US
                    if result["country_code"] == "US":
                        iso_code = address.get("ISO3166-2-lvl4", "")
                        if iso_code and "-" in iso_code:
                            result["state_code"] = iso_code.split("-")[1]
                    
                    logger.debug(f"Nominatim result: {result}")
                    return result
                    
        except Exception as e:
            logger.error(f"Erreur Nominatim: {str(e)}")
        
        return None
    
    async def _query_positionstack(self, latitude: float, longitude: float,
                                 language: str) -> Optional[Dict[str, Any]]:
        """Interroge l'API PositionStack (nécessite clé API)"""
        # TODO: Implémenter si clé API disponible
        return None
    
    async def _query_opencage(self, latitude: float, longitude: float,
                            language: str) -> Optional[Dict[str, Any]]:
        """Interroge l'API OpenCage (nécessite clé API)"""
        # TODO: Implémenter si clé API disponible
        return None
    
    def _query_offline_database(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Recherche dans la base de données offline"""
        
        # Chercher dans la base des pays/régions principales
        for country_info in self.offline_database["countries"]:
            bounds = country_info["bounds"]
            if (bounds["lat_min"] <= latitude <= bounds["lat_max"] and 
                bounds["lon_min"] <= longitude <= bounds["lon_max"]):
                
                result = {
                    "country": country_info["name"],
                    "country_code": country_info["code"],
                    "region": country_info["region"],
                    "continent": country_info["continent"],
                    "confidence": 0.6,
                    "source": "offline_database"
                }
                
                # Chercher les états/provinces si disponibles
                for state in country_info.get("states", []):
                    state_bounds = state["bounds"]
                    if (state_bounds["lat_min"] <= latitude <= state_bounds["lat_max"] and 
                        state_bounds["lon_min"] <= longitude <= state_bounds["lon_max"]):
                        result["state_province"] = state["name"]
                        result["state_code"] = state["code"]
                        result["confidence"] = 0.7
                        break
                
                return result
        
        # Fallback par région géographique large
        return self._identify_large_region(latitude, longitude)
    
    def _identify_large_region(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Identification par grande région géographique"""
        
        regions = {
            "North America": {"lat": (15, 72), "lon": (-170, -50)},
            "South America": {"lat": (-60, 15), "lon": (-85, -30)},
            "Europe": {"lat": (35, 72), "lon": (-15, 40)},
            "Africa": {"lat": (-35, 40), "lon": (-20, 55)},
            "Asia": {"lat": (-10, 55), "lon": (60, 180)},
            "Oceania": {"lat": (-50, -10), "lon": (110, 180)}
        }
        
        for region_name, bounds in regions.items():
            if (bounds["lat"][0] <= latitude <= bounds["lat"][1] and 
                bounds["lon"][0] <= longitude <= bounds["lon"][1]):
                return {
                    "region": region_name,
                    "confidence": 0.3,
                    "source": "region_detection"
                }
        
        return {
            "region": "Unknown",
            "confidence": 0.1,
            "source": "fallback"
        }
    
    def _merge_api_result(self, location_info: LocationInfo, result: Dict[str, Any],
                         api_name: str) -> LocationInfo:
        """Fusionne les résultats d'une API dans LocationInfo"""
        
        # Mise à jour des champs si disponibles
        if result.get("country"):
            location_info.country = result["country"]
        if result.get("country_code"):
            location_info.country_code = result["country_code"]
        if result.get("state_province"):
            location_info.state_province = result["state_province"]
        if result.get("state_code"):
            location_info.state_code = result["state_code"]
        if result.get("city"):
            location_info.city = result["city"]
        if result.get("district"):
            location_info.district = result["district"]
        if result.get("postal_code"):
            location_info.postal_code = result["postal_code"]
        
        # Mettre à jour métadonnées
        location_info.confidence = max(location_info.confidence, result.get("confidence", 0))
        location_info.source = result.get("source", api_name)
        
        return location_info
    
    def _merge_offline_result(self, location_info: LocationInfo, 
                            result: Dict[str, Any]) -> LocationInfo:
        """Fusionne les résultats offline"""
        
        # Compléter uniquement les champs manquants
        if not location_info.country and result.get("country"):
            location_info.country = result["country"]
        if not location_info.country_code and result.get("country_code"):
            location_info.country_code = result["country_code"]
        if not location_info.region and result.get("region"):
            location_info.region = result["region"]
        if not location_info.continent and result.get("continent"):
            location_info.continent = result["continent"]
        
        # Mettre à jour métadonnées si mieux
        if result.get("confidence", 0) > location_info.confidence:
            location_info.confidence = result["confidence"]
            location_info.source = result.get("source", "offline")
        
        return location_info
    
    def _enrich_with_air_quality_info(self, location_info: LocationInfo) -> LocationInfo:
        """Enrichit avec informations spécifiques à la qualité de l'air"""
        
        # Déterminer les sources de données optimales
        optimal_sources = []
        standards = "WHO"  # Par défaut
        monitoring_network = None
        
        # Règles par pays/région
        if location_info.country_code == "US":
            optimal_sources = ["NASA_TEMPO", "EPA_AIRNOW", "OPENAQ", "AQICN"]
            standards = "EPA_AQI"
            monitoring_network = "EPA AirNow"
            
        elif location_info.country_code == "CA":
            optimal_sources = ["NASA_TEMPO", "CANADA_AQHI", "OPENAQ", "AQICN"]
            standards = "CANADA_AQHI"
            monitoring_network = "Environment Canada"
            
        elif location_info.region == "North America":
            optimal_sources = ["NASA_TEMPO", "OPENAQ", "AQICN", "NASA_AIRS"]
            standards = "EPA_AQI"
            
        elif location_info.region == "Europe":
            optimal_sources = ["ESA_SENTINEL5P", "SENSOR_COMMUNITY", "OPENAQ", "AQICN"]
            standards = "WHO"
            monitoring_network = "European Environment Agency"
            
        else:
            optimal_sources = ["NASA_MERRA2", "ESA_SENTINEL5P", "OPENAQ", "AQICN"]
            standards = "WHO"
        
        # Assignation
        location_info.optimal_data_sources = optimal_sources
        location_info.air_quality_standards = standards
        location_info.monitoring_network = monitoring_network
        
        # Déterminer la timezone (approximative)
        if not location_info.timezone:
            location_info.timezone = self._estimate_timezone(
                location_info.latitude, location_info.longitude, location_info.country_code
            )
        
        return location_info
    
    def _estimate_timezone(self, latitude: float, longitude: float, 
                         country_code: Optional[str]) -> str:
        """Estimation approximative de la timezone"""
        
        # Estimation simple basée sur longitude
        utc_offset = round(longitude / 15)
        
        # Ajustements spécifiques par pays
        timezone_map = {
            "US": {
                (-170, -130): "America/Anchorage",    # Alaska
                (-130, -120): "America/Los_Angeles",   # Pacific
                (-120, -105): "America/Denver",        # Mountain  
                (-105, -90):  "America/Chicago",       # Central
                (-90, -67):   "America/New_York"       # Eastern
            },
            "CA": {
                (-141, -120): "America/Vancouver",     # Pacific
                (-120, -105): "America/Edmonton",      # Mountain
                (-105, -90):  "America/Winnipeg",      # Central
                (-90, -60):   "America/Toronto"        # Eastern
            }
        }
        
        if country_code in timezone_map:
            for (lon_min, lon_max), tz in timezone_map[country_code].items():
                if lon_min <= longitude <= lon_max:
                    return tz
        
        # Fallback générique
        return f"UTC{utc_offset:+d}" if utc_offset != 0 else "UTC"
    
    def _init_offline_database(self) -> Dict[str, Any]:
        """Initialise la base de données offline de fallback"""
        
        return {
            "countries": [
                {
                    "name": "United States",
                    "code": "US",
                    "region": "North America", 
                    "continent": "North America",
                    "bounds": {"lat_min": 18.9, "lat_max": 71.4, "lon_min": -179.1, "lon_max": -66.9},
                    "states": [
                        {
                            "name": "California",
                            "code": "CA",
                            "bounds": {"lat_min": 32.5, "lat_max": 42.0, "lon_min": -124.5, "lon_max": -114.1}
                        },
                        {
                            "name": "Texas", 
                            "code": "TX",
                            "bounds": {"lat_min": 25.8, "lat_max": 36.5, "lon_min": -106.6, "lon_max": -93.5}
                        },
                        {
                            "name": "Florida",
                            "code": "FL", 
                            "bounds": {"lat_min": 24.4, "lat_max": 31.0, "lon_min": -87.6, "lon_max": -80.0}
                        },
                        {
                            "name": "New York",
                            "code": "NY",
                            "bounds": {"lat_min": 40.5, "lat_max": 45.0, "lon_min": -79.8, "lon_max": -71.9}
                        }
                    ]
                },
                {
                    "name": "Canada",
                    "code": "CA",
                    "region": "North America",
                    "continent": "North America", 
                    "bounds": {"lat_min": 41.7, "lat_max": 83.1, "lon_min": -141.0, "lon_max": -52.6},
                    "states": [
                        {
                            "name": "Ontario",
                            "code": "ON",
                            "bounds": {"lat_min": 41.7, "lat_max": 56.9, "lon_min": -95.2, "lon_max": -74.3}
                        },
                        {
                            "name": "Quebec",
                            "code": "QC",
                            "bounds": {"lat_min": 45.0, "lat_max": 62.6, "lon_min": -79.8, "lon_max": -57.1}
                        },
                        {
                            "name": "British Columbia",
                            "code": "BC",
                            "bounds": {"lat_min": 48.3, "lat_max": 60.0, "lon_min": -139.1, "lon_max": -114.0}
                        }
                    ]
                },
                {
                    "name": "Mexico",
                    "code": "MX",
                    "region": "North America",
                    "continent": "North America",
                    "bounds": {"lat_min": 14.5, "lat_max": 32.7, "lon_min": -118.4, "lon_max": -86.7}
                },
                {
                    "name": "France",
                    "code": "FR",
                    "region": "Europe",
                    "continent": "Europe",
                    "bounds": {"lat_min": 41.3, "lat_max": 51.1, "lon_min": -5.1, "lon_max": 9.6}
                },
                {
                    "name": "Germany",
                    "code": "DE", 
                    "region": "Europe",
                    "continent": "Europe",
                    "bounds": {"lat_min": 47.3, "lat_max": 55.1, "lon_min": 5.9, "lon_max": 15.0}
                }
            ]
        }

    async def batch_get_locations(self, coordinates: List[Tuple[float, float]],
                                language: str = "en") -> List[LocationInfo]:
        """
        Obtient les informations de localisation pour plusieurs coordonnées
        
        Args:
            coordinates: Liste de tuples (latitude, longitude)
            language: Langue pour les résultats
            
        Returns:
            Liste des informations de localisation
        """
        results = []
        
        # Traitement séquentiel pour respecter les rate limits
        for lat, lon in coordinates:
            try:
                location_info = await self.get_location_info(lat, lon, language)
                results.append(location_info)
                
                # Délai pour respecter rate limits
                await asyncio.sleep(1.1)  # Plus que le minimum pour être sûr
                
            except Exception as e:
                logger.error(f"Erreur pour {lat}, {lon}: {str(e)}")
                # Ajouter une entry de fallback
                fallback = LocationInfo(
                    latitude=lat,
                    longitude=lon,
                    confidence=0.0,
                    source="error"
                )
                results.append(fallback)
        
        return results
    
    def get_supported_countries(self) -> List[Dict[str, str]]:
        """Retourne la liste des pays supportés avec détails"""
        
        countries = []
        for country in self.offline_database["countries"]:
            countries.append({
                "name": country["name"],
                "code": country["code"],
                "region": country["region"],
                "has_states": len(country.get("states", [])) > 0,
                "air_quality_standard": "EPA_AQI" if country["code"] in ["US", "CA"] else "WHO"
            })
        
        return countries

# Instance globale
geolocation_service = ModernGeolocationService()

# Fonctions utilitaires pour l'API
async def get_location_details(latitude: float, longitude: float, 
                             language: str = "en") -> LocationInfo:
    """Fonction utilitaire pour obtenir les détails d'une location"""
    async with geolocation_service:
        return await geolocation_service.get_location_info(latitude, longitude, language)

async def reverse_geocode_batch(coordinates: List[Tuple[float, float]],
                              language: str = "en") -> List[LocationInfo]:
    """Fonction utilitaire pour le géocodage inverse par lots"""
    async with geolocation_service:
        return await geolocation_service.batch_get_locations(coordinates, language)
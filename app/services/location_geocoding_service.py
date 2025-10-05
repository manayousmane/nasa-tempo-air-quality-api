"""
🌍 SERVICE GÉOCODAGE POUR TEMPO
================================================================================
Service pour convertir noms de pays/états/provinces en coordonnées TEMPO
================================================================================
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LocationData:
    """Structure de données pour une location"""
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
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    last_updated: str = ""

class LocationGeocodingService:
    """Service pour géocoder des noms de lieux"""
    
    def __init__(self):
        self.nominatim_base = "https://nominatim.openstreetmap.org"
        self.session = None
        
        # Base de données des principales villes en Amérique du Nord
        self.na_locations = {
            # États-Unis - Principales villes
            "new york": {"lat": 40.7128, "lon": -74.0060, "country": "United States", "state": "New York"},
            "los angeles": {"lat": 34.0522, "lon": -118.2437, "country": "United States", "state": "California"},
            "chicago": {"lat": 41.8781, "lon": -87.6298, "country": "United States", "state": "Illinois"},
            "houston": {"lat": 29.7604, "lon": -95.3698, "country": "United States", "state": "Texas"},
            "phoenix": {"lat": 33.4484, "lon": -112.0740, "country": "United States", "state": "Arizona"},
            "philadelphia": {"lat": 39.9526, "lon": -75.1652, "country": "United States", "state": "Pennsylvania"},
            "san antonio": {"lat": 29.4241, "lon": -98.4936, "country": "United States", "state": "Texas"},
            "san diego": {"lat": 32.7157, "lon": -117.1611, "country": "United States", "state": "California"},
            "dallas": {"lat": 32.7767, "lon": -96.7970, "country": "United States", "state": "Texas"},
            "san jose": {"lat": 37.3382, "lon": -121.8863, "country": "United States", "state": "California"},
            "austin": {"lat": 30.2672, "lon": -97.7431, "country": "United States", "state": "Texas"},
            "miami": {"lat": 25.7617, "lon": -80.1918, "country": "United States", "state": "Florida"},
            "atlanta": {"lat": 33.7490, "lon": -84.3880, "country": "United States", "state": "Georgia"},
            "boston": {"lat": 42.3601, "lon": -71.0589, "country": "United States", "state": "Massachusetts"},
            "seattle": {"lat": 47.6062, "lon": -122.3321, "country": "United States", "state": "Washington"},
            "denver": {"lat": 39.7392, "lon": -104.9903, "country": "United States", "state": "Colorado"},
            "las vegas": {"lat": 36.1699, "lon": -115.1398, "country": "United States", "state": "Nevada"},
            "detroit": {"lat": 42.3314, "lon": -83.0458, "country": "United States", "state": "Michigan"},
            
            # Canada - Principales villes
            "toronto": {"lat": 43.6532, "lon": -79.3832, "country": "Canada", "state": "Ontario"},
            "montreal": {"lat": 45.5017, "lon": -73.5673, "country": "Canada", "state": "Quebec"},
            "vancouver": {"lat": 49.2827, "lon": -123.1207, "country": "Canada", "state": "British Columbia"},
            "calgary": {"lat": 51.0447, "lon": -114.0719, "country": "Canada", "state": "Alberta"},
            "edmonton": {"lat": 53.5461, "lon": -113.4938, "country": "Canada", "state": "Alberta"},
            "ottawa": {"lat": 45.4215, "lon": -75.6972, "country": "Canada", "state": "Ontario"},
            "winnipeg": {"lat": 49.8951, "lon": -97.1384, "country": "Canada", "state": "Manitoba"},
            "quebec city": {"lat": 46.8139, "lon": -71.2080, "country": "Canada", "state": "Quebec"},
            
            # États/Provinces entiers (coordonnées centrales)
            "california": {"lat": 36.7783, "lon": -119.4179, "country": "United States", "state": "California"},
            "texas": {"lat": 31.9686, "lon": -99.9018, "country": "United States", "state": "Texas"},
            "florida": {"lat": 27.7663, "lon": -81.6868, "country": "United States", "state": "Florida"},
            "new york state": {"lat": 43.2994, "lon": -74.2179, "country": "United States", "state": "New York"},
            "ontario": {"lat": 50.0000, "lon": -85.0000, "country": "Canada", "state": "Ontario"},
            "quebec": {"lat": 53.0000, "lon": -70.0000, "country": "Canada", "state": "Quebec"},
            "british columbia": {"lat": 55.0000, "lon": -125.0000, "country": "Canada", "state": "British Columbia"},
            "alberta": {"lat": 55.0000, "lon": -115.0000, "country": "Canada", "state": "Alberta"},
            
            # Pays
            "united states": {"lat": 45.0000, "lon": -100.0000, "country": "United States", "state": ""},
            "usa": {"lat": 45.0000, "lon": -100.0000, "country": "United States", "state": ""},
            "canada": {"lat": 56.0000, "lon": -106.0000, "country": "Canada", "state": ""},
        }
    
    async def get_session(self):
        """Obtient une session HTTP async"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def is_in_tempo_coverage(self, lat: float, lon: float) -> bool:
        """Vérifie si les coordonnées sont dans la zone TEMPO"""
        return (40.0 <= lat <= 70.0 and -130.0 <= lon <= -70.0)
    
    async def geocode_location(self, location_name: str) -> Optional[Dict[str, Any]]:
        """Géocode une location par nom"""
        try:
            # Normaliser le nom
            normalized_name = location_name.lower().strip()
            
            # Chercher d'abord dans la base locale
            if normalized_name in self.na_locations:
                local_data = self.na_locations[normalized_name]
                return {
                    "name": location_name.title(),
                    "latitude": local_data["lat"],
                    "longitude": local_data["lon"],
                    "country": local_data["country"],
                    "state": local_data["state"],
                    "source": "local_database"
                }
            
            # Pour les locations non dans la base locale, ne pas faire d'appel réseau
            # car nous nous concentrons sur l'Amérique du Nord TEMPO
            logger.info(f"Location '{location_name}' non trouvée dans base locale TEMPO")
            return None
            
            # Note: Le code Nominatim est désactivé pour éviter les erreurs réseau
            # et se concentrer sur les locations pré-configurées pour TEMPO
            
        except Exception as e:
            logger.error(f"Erreur géocodage {location_name}: {str(e)}")
            return None
    
    async def search_multiple_locations(self, location_names: List[str]) -> List[Dict[str, Any]]:
        """Géocode plusieurs locations"""
        results = []
        
        for location_name in location_names:
            result = await self.geocode_location(location_name)
            if result:
                results.append(result)
            
            # Petit délai pour éviter de surcharger Nominatim
            await asyncio.sleep(0.1)
        
        return results
    
    def get_suggested_locations(self, query: str = "") -> List[str]:
        """Retourne des suggestions de locations basées sur la query"""
        query_lower = query.lower()
        
        suggestions = []
        for location in self.na_locations.keys():
            if query_lower in location or location.startswith(query_lower):
                suggestions.append(location.title())
        
        return sorted(suggestions)[:10]  # Top 10
    
    def get_all_available_locations(self) -> List[Dict[str, Any]]:
        """Retourne toutes les locations disponibles"""
        locations = []
        
        for name, data in self.na_locations.items():
            locations.append({
                "name": name.title(),
                "coordinates": [data["lat"], data["lon"]],
                "country": data["country"],
                "state": data["state"],
                "in_tempo_coverage": self.is_in_tempo_coverage(data["lat"], data["lon"])
            })
        
        return sorted(locations, key=lambda x: (x["country"], x["state"], x["name"]))

# Instance globale
location_service = LocationGeocodingService()
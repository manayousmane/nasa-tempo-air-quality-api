"""
Service de géolocalisation performante
Résolution des noms de localités avec multiple sources
"""

import aiohttp
import asyncio
from typing import Dict, Optional, Tuple
import logging
import json
import math

logger = logging.getLogger(__name__)

class AdvancedGeolocationService:
    """Service avancé de géolocalisation avec sources multiples"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Base de données étendue des villes mondiales
        self.major_cities = [
            # Europe
            (48.8566, 2.3522, "Paris", "France"),
            (51.5074, -0.1278, "Londres", "Royaume-Uni"),
            (52.5200, 13.4050, "Berlin", "Allemagne"),
            (41.9028, 12.4964, "Rome", "Italie"),
            (40.4168, -3.7038, "Madrid", "Espagne"),
            (59.3293, 18.0686, "Stockholm", "Suède"),
            (55.7558, 37.6176, "Moscou", "Russie"),
            (50.0755, 14.4378, "Prague", "République tchèque"),
            (47.4979, 19.0402, "Budapest", "Hongrie"),
            (52.3676, 4.9041, "Amsterdam", "Pays-Bas"),
            (60.1699, 24.9384, "Helsinki", "Finlande"),
            (45.4642, 9.1900, "Milan", "Italie"),
            
            # Amérique du Nord
            (40.7128, -74.0060, "New York", "États-Unis"),
            (34.0522, -118.2437, "Los Angeles", "États-Unis"),
            (41.8781, -87.6298, "Chicago", "États-Unis"),
            (43.6532, -79.3832, "Toronto", "Canada"),
            (45.5017, -73.5673, "Montréal", "Canada"),
            (49.2827, -123.1207, "Vancouver", "Canada"),
            (25.7617, -80.1918, "Miami", "États-Unis"),
            (32.7767, -96.7970, "Dallas", "États-Unis"),
            (29.7604, -95.3698, "Houston", "États-Unis"),
            (19.4326, -99.1332, "Mexico", "Mexique"),
            
            # Amérique du Sud
            (-23.5505, -46.6333, "São Paulo", "Brésil"),
            (-22.9068, -43.1729, "Rio de Janeiro", "Brésil"),
            (-34.6118, -58.3960, "Buenos Aires", "Argentine"),
            (-33.4489, -70.6693, "Santiago", "Chili"),
            (4.7110, -74.0721, "Bogotá", "Colombie"),
            (-12.0464, -77.0428, "Lima", "Pérou"),
            
            # Asie
            (35.6762, 139.6503, "Tokyo", "Japon"),
            (39.9042, 116.4074, "Pékin", "Chine"),
            (31.2304, 121.4737, "Shanghai", "Chine"),
            (28.6139, 77.2090, "New Delhi", "Inde"),
            (19.0760, 72.8777, "Mumbai", "Inde"),
            (1.3521, 103.8198, "Singapour", "Singapour"),
            (37.5665, 126.9780, "Séoul", "Corée du Sud"),
            (25.2048, 55.2708, "Dubaï", "Émirats arabes unis"),
            (35.6892, 51.3890, "Téhéran", "Iran"),
            (33.6844, 73.0479, "Islamabad", "Pakistan"),
            (23.8103, 90.4125, "Dhaka", "Bangladesh"),
            (14.5995, 120.9842, "Manille", "Philippines"),
            (13.7563, 100.5018, "Bangkok", "Thaïlande"),
            (21.0285, 105.8542, "Hanoï", "Vietnam"),
            (10.8231, 106.6297, "Hô Chi Minh-Ville", "Vietnam"),
            (-6.2088, 106.8456, "Jakarta", "Indonésie"),
            (3.1390, 101.6869, "Kuala Lumpur", "Malaisie"),
            
            # Afrique
            (30.0444, 31.2357, "Le Caire", "Égypte"),
            (-26.2041, 28.0473, "Johannesburg", "Afrique du Sud"),
            (-33.9249, 18.4241, "Le Cap", "Afrique du Sud"),
            (6.5244, 3.3792, "Lagos", "Nigeria"),
            (9.0579, 7.4951, "Abuja", "Nigeria"),
            (-1.2921, 36.8219, "Nairobi", "Kenya"),
            (33.8869, 9.5375, "Tunis", "Tunisie"),
            (-29.8587, 31.0218, "Durban", "Afrique du Sud"),
            
            # Océanie
            (-33.8688, 151.2093, "Sydney", "Australie"),
            (-37.8136, 144.9631, "Melbourne", "Australie"),
            (-27.4698, 153.0251, "Brisbane", "Australie"),
            (-31.9505, 115.8605, "Perth", "Australie"),
            (-36.8485, 174.7633, "Auckland", "Nouvelle-Zélande"),
            (-41.2865, 174.7762, "Wellington", "Nouvelle-Zélande"),
            
            # Autres grandes villes importantes
            (55.6761, 12.5683, "Copenhague", "Danemark"),
            (59.9139, 10.7522, "Oslo", "Norvège"),
            (64.1466, -21.9426, "Reykjavik", "Islande"),
            (39.3999, 116.7278, "Pékin", "Chine"),
            (22.3193, 114.1694, "Hong Kong", "Hong Kong"),
            (22.1987, 113.5439, "Macao", "Macao"),
            (25.0330, 121.5654, "Taipei", "Taïwan"),
        ]
        
        # Régions géographiques pour estimations
        self.geographical_regions = {
            "Europe de l'Ouest": (50.0, 10.0, 35.0, 60.0, -10.0, 30.0),
            "Europe de l'Est": (50.0, 30.0, 35.0, 70.0, 15.0, 50.0),
            "Amérique du Nord": (45.0, -100.0, 20.0, 70.0, -170.0, -50.0),
            "Amérique Centrale": (20.0, -90.0, 5.0, 35.0, -120.0, -60.0),
            "Amérique du Sud": (-15.0, -60.0, -60.0, 15.0, -85.0, -30.0),
            "Asie de l'Est": (35.0, 110.0, 15.0, 55.0, 95.0, 145.0),
            "Asie du Sud": (25.0, 80.0, 5.0, 40.0, 65.0, 95.0),
            "Asie du Sud-Est": (10.0, 110.0, -15.0, 25.0, 90.0, 145.0),
            "Moyen-Orient": (30.0, 45.0, 15.0, 45.0, 25.0, 65.0),
            "Afrique du Nord": (25.0, 15.0, 15.0, 40.0, -20.0, 50.0),
            "Afrique Subsaharienne": (-5.0, 20.0, -35.0, 20.0, -20.0, 50.0),
            "Océanie": (-25.0, 140.0, -50.0, -5.0, 110.0, 180.0),
            "Arctique": (70.0, 0.0, 60.0, 90.0, -180.0, 180.0),
            "Antarctique": (-70.0, 0.0, -90.0, -60.0, -180.0, 180.0)
        }
    
    async def __aenter__(self):
        """Initialise la session HTTP"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            headers = {
                'User-Agent': 'NASA-TEMPO-Air-Quality-API/2.0',
                'Accept': 'application/json'
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcule la distance en kilomètres entre deux points (formule haversine)"""
        # Convertir en radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Formule haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Rayon de la Terre en km
        r = 6371
        return c * r
    
    def find_closest_major_city(self, latitude: float, longitude: float, max_distance: float = 100.0) -> Optional[Tuple[str, str, float]]:
        """Trouve la ville majeure la plus proche dans un rayon donné"""
        closest_city = None
        min_distance = float('inf')
        
        for city_lat, city_lon, city_name, country in self.major_cities:
            distance = self.calculate_distance(latitude, longitude, city_lat, city_lon)
            
            if distance <= max_distance and distance < min_distance:
                min_distance = distance
                closest_city = (city_name, country, distance)
        
        return closest_city
    
    def determine_geographical_region(self, latitude: float, longitude: float) -> str:
        """Détermine la région géographique basée sur les coordonnées"""
        for region_name, (center_lat, center_lon, min_lat, max_lat, min_lon, max_lon) in self.geographical_regions.items():
            if min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon:
                return region_name
        
        # Régions spéciales
        if latitude > 60:
            return "Régions Arctiques"
        elif latitude < -60:
            return "Régions Antarctiques"
        elif abs(latitude) < 23.5:
            return "Régions Tropicales"
        elif 23.5 <= abs(latitude) < 35:
            return "Régions Subtropicales"
        else:
            return "Régions Tempérées"
    
    def get_country_from_coordinates(self, latitude: float, longitude: float) -> str:
        """Estime le pays basé sur les coordonnées (logique simplifiée)"""
        # Logique simplifiée pour les principaux pays
        
        # Europe
        if 35 <= latitude <= 70 and -10 <= longitude <= 30:
            if 42 <= latitude <= 51 and -5 <= longitude <= 9:
                return "France"
            elif 47 <= latitude <= 55 and 5 <= longitude <= 15:
                return "Allemagne"
            elif 50 <= latitude <= 60 and -8 <= longitude <= 2:
                return "Royaume-Uni"
            elif 39 <= latitude <= 47 and 6 <= longitude <= 19:
                return "Italie"
            elif 36 <= latitude <= 44 and -10 <= longitude <= 4:
                return "Espagne"
            else:
                return "Europe"
        
        # Amérique du Nord
        elif 25 <= latitude <= 70 and -170 <= longitude <= -50:
            if latitude >= 45:
                return "Canada"
            else:
                return "États-Unis"
        
        # Amérique du Sud
        elif -60 <= latitude <= 15 and -85 <= longitude <= -30:
            if -35 <= latitude <= 5 and -75 <= longitude <= -35:
                return "Brésil"
            elif -56 <= latitude <= -21 and -74 <= longitude <= -53:
                return "Argentine"
            else:
                return "Amérique du Sud"
        
        # Asie
        elif 5 <= latitude <= 55 and 65 <= longitude <= 145:
            if 15 <= latitude <= 45 and 73 <= longitude <= 135:
                return "Chine"
            elif 8 <= latitude <= 37 and 68 <= longitude <= 97:
                return "Inde"
            elif 30 <= latitude <= 46 and 129 <= longitude <= 146:
                return "Japon"
            else:
                return "Asie"
        
        # Afrique
        elif -35 <= latitude <= 40 and -20 <= longitude <= 55:
            return "Afrique"
        
        # Océanie
        elif -50 <= latitude <= -5 and 110 <= longitude <= 180:
            return "Australie"
        
        return "Région inconnue"
    
    async def reverse_geocode_nominatim(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Géocodage inverse via Nominatim (OpenStreetMap)"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'zoom': 10,
                'addressdetails': 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(f"Nominatim error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur Nominatim: {e}")
            return None
    
    def format_location_name(self, geocoding_data: Optional[Dict], latitude: float, longitude: float) -> str:
        """Formate le nom de localisation avec priorité sur les données de géocodage"""
        
        # 1. Essayer d'utiliser les données de géocodage Nominatim
        if geocoding_data:
            address = geocoding_data.get('address', {})
            display_name = geocoding_data.get('display_name', '')
            
            # Extraire les composants principaux
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('municipality') or
                   address.get('county'))
            
            state = (address.get('state') or 
                    address.get('province') or
                    address.get('region'))
            
            country = address.get('country')
            
            # Construire le nom formaté
            location_parts = []
            if city:
                location_parts.append(city)
            elif state:
                location_parts.append(state)
            
            if country:
                location_parts.append(country)
            
            if location_parts:
                return ", ".join(location_parts)
            elif display_name:
                # Utiliser display_name mais le raccourcir
                parts = display_name.split(', ')
                if len(parts) >= 2:
                    return f"{parts[0]}, {parts[-1]}"
                return parts[0] if parts else display_name
        
        # 2. Chercher une ville majeure proche
        closest_city = self.find_closest_major_city(latitude, longitude, max_distance=50.0)
        if closest_city:
            city_name, country, distance = closest_city
            if distance <= 25:
                return f"{city_name}, {country}"
            else:
                return f"Près de {city_name}, {country}"
        
        # 3. Chercher une ville majeure dans un rayon plus large
        closest_city_wide = self.find_closest_major_city(latitude, longitude, max_distance=200.0)
        if closest_city_wide:
            city_name, country, distance = closest_city_wide
            return f"Région de {city_name}, {country}"
        
        # 4. Utiliser la région géographique et le pays estimé
        region = self.determine_geographical_region(latitude, longitude)
        country = self.get_country_from_coordinates(latitude, longitude)
        
        if country != "Région inconnue":
            return f"{region}, {country}"
        else:
            return f"{region} ({latitude:.3f}°, {longitude:.3f}°)"
    
    async def get_enhanced_location_name(self, latitude: float, longitude: float) -> str:
        """
        Méthode principale pour obtenir un nom de localisation performant
        Combine géocodage en ligne et base de données locale
        """
        try:
            # Vérification rapide des villes majeures d'abord (cache local)
            closest_city = self.find_closest_major_city(latitude, longitude, max_distance=10.0)
            if closest_city:
                city_name, country, distance = closest_city
                if distance <= 5:  # Très proche d'une ville majeure
                    return f"{city_name}, {country}"
            
            # Géocodage en ligne pour plus de précision
            geocoding_data = await self.reverse_geocode_nominatim(latitude, longitude)
            
            # Formater le résultat
            return self.format_location_name(geocoding_data, latitude, longitude)
            
        except Exception as e:
            logger.error(f"Erreur lors de la géolocalisation: {e}")
            # Fallback vers la méthode locale uniquement
            return self.format_location_name(None, latitude, longitude)
    
    def get_location_info(self, latitude: float, longitude: float) -> Dict:
        """Retourne des informations détaillées sur la localisation"""
        
        # Ville majeure la plus proche
        closest_city = self.find_closest_major_city(latitude, longitude, max_distance=200.0)
        
        # Région géographique
        region = self.determine_geographical_region(latitude, longitude)
        
        # Pays estimé
        country = self.get_country_from_coordinates(latitude, longitude)
        
        # Type de zone (approximatif)
        zone_type = "urbaine" if closest_city and closest_city[2] <= 50 else "rurale"
        
        info = {
            "region": region,
            "country": country,
            "zone_type": zone_type,
            "closest_major_city": {
                "name": closest_city[0] if closest_city else None,
                "country": closest_city[1] if closest_city else None,
                "distance_km": round(closest_city[2], 1) if closest_city else None
            } if closest_city else None
        }
        
        return info

# Instance globale pour utilisation dans l'API
geolocation_service = AdvancedGeolocationService()
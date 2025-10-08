"""
CONNECTEUR API RÉEL - Remplace les simulations par de vraies données
"""

import aiohttp
import asyncio
import json
import logging
import math
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class RealAPIConnector:
    """
    Connecteur pour VRAIES APIs de qualité de l'air
    - OpenAQ v3 (nouvelle version)
    - PurpleAir (réseau de capteurs)
    - AirNow EPA (données officielles USA)
    - IQAir (service premium)
    - NASA Earthdata (données satellitaires)
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configuration des clés API (à définir dans vos variables d'environnement)
        self.openaq_api_key = os.getenv('OPENAQ_API_KEY')
        self.purpleair_api_key = os.getenv('PURPLEAIR_API_KEY')
        self.airnow_api_key = os.getenv('AIRNOW_API_KEY')
        self.iqair_api_key = os.getenv('IQAIR_API_KEY')
        self.nasa_earthdata_username = os.getenv('NASA_EARTHDATA_USERNAME')
        self.nasa_earthdata_password = os.getenv('NASA_EARTHDATA_PASSWORD')
        
        logger.info("🔗 Initialisation du connecteur API réel")
        self._log_available_apis()
    
    def _log_available_apis(self):
        """Log quelles APIs sont configurées"""
        apis_status = {
            'OpenAQ v3': bool(self.openaq_api_key),
            'PurpleAir': bool(self.purpleair_api_key),
            'AirNow EPA': bool(self.airnow_api_key),
            'IQAir': bool(self.iqair_api_key),
            'NASA Earthdata': bool(self.nasa_earthdata_username and self.nasa_earthdata_password)
        }
        
        configured = [name for name, configured in apis_status.items() if configured]
        missing = [name for name, configured in apis_status.items() if not configured]
        
        if configured:
            logger.info(f"✅ APIs configurées: {', '.join(configured)}")
        if missing:
            logger.warning(f"⚠️ APIs manquantes: {', '.join(missing)}")
    
    async def __aenter__(self):
        """Initialise la session HTTP"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'NASA-TEMPO-Real-API/2.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()
    
    # ==========================================
    # 1. OPENAQ V3 (NOUVELLE VERSION)
    # ==========================================
    
    async def get_openaq_v3_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Récupère les données réelles d'OpenAQ v3
        Documentation: https://docs.openaq.org/
        """
        if not self.openaq_api_key:
            logger.warning("❌ Clé API OpenAQ v3 manquante")
            return None
        
        try:
            logger.info(f"🌐 Récupération OpenAQ v3 pour {latitude}, {longitude}")
            
            # Étape 1: Trouver les stations proches
            locations_url = "https://api.openaq.org/v3/locations"
            headers = {
                'X-API-Key': self.openaq_api_key,
                'Content-Type': 'application/json'
            }
            
            params = {
                'coordinates': f"{latitude},{longitude}",
                'radius': 50000,  # 50km de rayon
                'limit': 20,
                'order_by': 'distance',
                'has_latest': 'true'  # Seulement les stations avec données récentes
            }
            
            async with self.session.get(locations_url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"OpenAQ v3 locations error: {response.status}")
                    return None
                
                locations_data = await response.json()
                locations = locations_data.get('results', [])
                
                if not locations:
                    logger.warning("OpenAQ v3: Aucune station trouvée dans la zone")
                    return None
                
                # Prendre la station la plus proche avec le plus de données
                best_location = None
                best_score = -1
                
                for location in locations:
                    # Score basé sur la distance et le nombre de paramètres
                    distance = location.get('distance', float('inf'))
                    parameter_count = len(location.get('parameters', []))
                    score = parameter_count * 100 - distance / 1000  # Favorise plus de données et proximité
                    
                    if score > best_score:
                        best_score = score
                        best_location = location
                
                if not best_location:
                    return None
                
                # Étape 2: Récupérer les mesures actuelles
                location_id = best_location['id']
                latest_url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
                
                async with self.session.get(latest_url, headers=headers) as measurements_response:
                    if measurements_response.status != 200:
                        logger.error(f"OpenAQ v3 measurements error: {measurements_response.status}")
                        return None
                    
                    measurements_data = await measurements_response.json()
                    measurements = measurements_data.get('results', [])
                    
                    if not measurements:
                        logger.warning("OpenAQ v3: Pas de mesures récentes")
                        return None
                    
                    # Parser les données
                    return self._format_openaq_v3_data(best_location, measurements, latitude, longitude)
        
        except Exception as e:
            logger.error(f"Erreur OpenAQ v3: {e}")
            return None
    
    def _format_openaq_v3_data(self, location: Dict, measurements: List[Dict], target_lat: float, target_lon: float) -> Dict:
        """Formate les données OpenAQ v3 en format standard"""
        
        # Organiser les mesures par paramètre
        pollutants = {}
        last_updated = None
        
        for measurement in measurements:
            parameter = measurement.get('parameter', '').lower()
            value = measurement.get('value')
            date_time = measurement.get('datetime')
            
            if parameter and value is not None:
                pollutants[parameter] = float(value)
                if date_time and (not last_updated or date_time > last_updated):
                    last_updated = date_time
        
        # Calcul de l'AQI
        aqi = self._calculate_aqi_from_pollutants(pollutants)
        
        # Coordonnées de la station
        station_coords = location.get('coordinates', {})
        station_lat = station_coords.get('latitude', target_lat)
        station_lon = station_coords.get('longitude', target_lon)
        
        # Distance de la station
        distance_km = self._calculate_distance(target_lat, target_lon, station_lat, station_lon)
        
        return {
            'name': location.get('name', 'Station OpenAQ'),
            'city': location.get('city', 'Unknown'),
            'country': location.get('country', 'Unknown'),
            'coordinates': [target_lat, target_lon],
            'station_coordinates': [station_lat, station_lon],
            'station_distance_km': round(distance_km, 2),
            'aqi': aqi,
            'pm25': pollutants.get('pm25', pollutants.get('pm2.5', 0)),
            'pm10': pollutants.get('pm10', 0),
            'no2': pollutants.get('no2', 0),
            'o3': pollutants.get('o3', 0),
            'so2': pollutants.get('so2', 0),
            'co': pollutants.get('co', 0),
            'data_source': 'OpenAQ v3 Real Data',
            'station_id': location.get('id'),
            'last_updated': last_updated or datetime.utcnow().isoformat() + "Z",
            'data_quality': 'high',
            'pollutants_available': list(pollutants.keys())
        }
    
    # ==========================================
    # 2. PURPLEAIR (RÉSEAU DE CAPTEURS)
    # ==========================================
    
    async def get_purpleair_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Récupère les données réelles de PurpleAir
        Documentation: https://api.purpleair.com/
        """
        if not self.purpleair_api_key:
            logger.warning("❌ Clé API PurpleAir manquante")
            return None
        
        try:
            logger.info(f"🟣 Récupération PurpleAir pour {latitude}, {longitude}")
            
            url = "https://api.purpleair.com/v1/sensors"
            headers = {
                'X-API-Key': self.purpleair_api_key
            }
            
            # Zone de recherche (rectangle autour du point)
            margin = 0.1  # ~11km
            params = {
                'nwlat': latitude + margin,
                'nwlng': longitude - margin,
                'selat': latitude - margin,
                'selng': longitude + margin,
                'fields': 'pm2.5_atm,pm2.5_cf_1,pm10.0_atm,temperature,humidity,pressure,name,latitude,longitude,last_seen'
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"PurpleAir error: {response.status}")
                    return None
                
                data = await response.json()
                sensors = data.get('data', [])
                
                if not sensors:
                    logger.warning("PurpleAir: Aucun capteur trouvé dans la zone")
                    return None
                
                # Trouver le capteur le plus proche
                closest_sensor = None
                min_distance = float('inf')
                
                fields = data.get('fields', [])
                lat_idx = fields.index('latitude') if 'latitude' in fields else None
                lon_idx = fields.index('longitude') if 'longitude' in fields else None
                
                if lat_idx is None or lon_idx is None:
                    logger.error("PurpleAir: Coordonnées manquantes")
                    return None
                
                for sensor in sensors:
                    if len(sensor) > max(lat_idx, lon_idx):
                        sensor_lat = sensor[lat_idx]
                        sensor_lon = sensor[lon_idx]
                        
                        if sensor_lat and sensor_lon:
                            distance = self._calculate_distance(latitude, longitude, sensor_lat, sensor_lon)
                            if distance < min_distance:
                                min_distance = distance
                                closest_sensor = sensor
                
                if not closest_sensor:
                    return None
                
                return self._format_purpleair_data(closest_sensor, fields, latitude, longitude, min_distance)
        
        except Exception as e:
            logger.error(f"Erreur PurpleAir: {e}")
            return None
    
    def _format_purpleair_data(self, sensor: List, fields: List[str], target_lat: float, target_lon: float, distance: float) -> Dict:
        """Formate les données PurpleAir en format standard"""
        
        # Créer un dictionnaire des valeurs
        sensor_data = dict(zip(fields, sensor))
        
        # Extraire les polluants
        pm25 = sensor_data.get('pm2.5_atm', 0) or 0
        pm10 = sensor_data.get('pm10.0_atm', 0) or 0
        
        # PurpleAir se concentre sur PM, estimer les autres
        estimated_no2 = pm25 * 0.3  # Estimation basée sur corrélation
        estimated_o3 = 50 + pm25 * 0.8  # Estimation
        
        # Calcul AQI basé sur PM2.5 principalement
        aqi = self._calculate_aqi_from_pm25(pm25)
        
        return {
            'name': sensor_data.get('name', 'PurpleAir Sensor'),
            'coordinates': [target_lat, target_lon],
            'station_coordinates': [sensor_data.get('latitude', target_lat), sensor_data.get('longitude', target_lon)],
            'station_distance_km': round(distance, 2),
            'aqi': aqi,
            'pm25': round(pm25, 1),
            'pm10': round(pm10, 1),
            'no2': round(estimated_no2, 1),  # Estimé
            'o3': round(estimated_o3, 1),   # Estimé
            'so2': 5.0,  # Valeur par défaut
            'co': 1.0,   # Valeur par défaut
            'temperature': sensor_data.get('temperature', 20),
            'humidity': sensor_data.get('humidity', 50),
            'pressure': sensor_data.get('pressure', 1013),
            'data_source': 'PurpleAir Real Data',
            'last_seen': sensor_data.get('last_seen'),
            'data_quality': 'high',
            'notes': 'PM2.5/PM10 from sensor, NO2/O3 estimated'
        }
    
    # ==========================================
    # 3. AIRNOW EPA (DONNÉES OFFICIELLES USA)
    # ==========================================
    
    async def get_airnow_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Récupère les données réelles d'AirNow EPA
        Documentation: https://docs.airnowapi.org/
        """
        if not self.airnow_api_key:
            logger.warning("❌ Clé API AirNow EPA manquante")
            return None
        
        try:
            logger.info(f"🇺🇸 Récupération AirNow EPA pour {latitude}, {longitude}")
            
            # AirNow utilise un format spécifique
            url = "https://www.airnowapi.org/aq/observation/latLong/current/"
            
            params = {
                'format': 'application/json',
                'latitude': latitude,
                'longitude': longitude,
                'distance': 50,  # rayon en miles
                'API_KEY': self.airnow_api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"AirNow EPA error: {response.status}")
                    return None
                
                data = await response.json()
                
                if not data:
                    logger.warning("AirNow EPA: Aucune donnée trouvée")
                    return None
                
                return self._format_airnow_data(data, latitude, longitude)
        
        except Exception as e:
            logger.error(f"Erreur AirNow EPA: {e}")
            return None
    
    def _format_airnow_data(self, data: List[Dict], target_lat: float, target_lon: float) -> Dict:
        """Formate les données AirNow EPA en format standard"""
        
        pollutants = {}
        station_info = {}
        
        for observation in data:
            parameter = observation.get('ParameterName', '').lower()
            aqi_value = observation.get('AQI')
            
            # Mapper les noms de paramètres EPA
            if 'pm2.5' in parameter:
                pollutants['pm25_aqi'] = aqi_value
            elif 'pm10' in parameter:
                pollutants['pm10_aqi'] = aqi_value
            elif 'ozone' in parameter or 'o3' in parameter:
                pollutants['o3_aqi'] = aqi_value
            
            # Informations de la station
            if not station_info:
                station_info = {
                    'name': observation.get('ReportingArea', 'EPA Station'),
                    'state': observation.get('StateCode', ''),
                    'date': observation.get('DateObserved', ''),
                    'hour': observation.get('HourObserved', '')
                }
        
        # Prendre la valeur AQI la plus élevée
        aqi = max([v for v in pollutants.values() if v is not None] or [50])
        
        return {
            'name': station_info.get('name', 'EPA Station'),
            'state': station_info.get('state'),
            'coordinates': [target_lat, target_lon],
            'aqi': aqi,
            'pm25': self._aqi_to_concentration('pm25', pollutants.get('pm25_aqi', 0)),
            'pm10': self._aqi_to_concentration('pm10', pollutants.get('pm10_aqi', 0)),
            'o3': self._aqi_to_concentration('o3', pollutants.get('o3_aqi', 0)),
            'no2': 15.0,  # Non fourni par AirNow, estimation
            'so2': 5.0,   # Non fourni par AirNow, estimation
            'co': 1.0,    # Non fourni par AirNow, estimation
            'data_source': 'AirNow EPA Real Data',
            'observation_date': station_info.get('date'),
            'observation_hour': station_info.get('hour'),
            'data_quality': 'official',
            'coverage': 'USA only'
        }
    
    # ==========================================
    # 4. IQAIR (SERVICE PREMIUM)
    # ==========================================
    
    async def get_iqair_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Récupère les données réelles d'IQAir
        Documentation: https://www.iqair.com/air-pollution-data-api
        """
        if not self.iqair_api_key:
            logger.warning("❌ Clé API IQAir manquante")
            return None
        
        try:
            logger.info(f"🌍 Récupération IQAir pour {latitude}, {longitude}")
            
            url = "https://api.airvisual.com/v2/nearest_city"
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'key': self.iqair_api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"IQAir error: {response.status}")
                    return None
                
                data = await response.json()
                
                if data.get('status') != 'success':
                    logger.warning(f"IQAir API error: {data.get('data', 'Unknown error')}")
                    return None
                
                return self._format_iqair_data(data['data'], latitude, longitude)
        
        except Exception as e:
            logger.error(f"Erreur IQAir: {e}")
            return None
    
    def _format_iqair_data(self, data: Dict, target_lat: float, target_lon: float) -> Dict:
        """Formate les données IQAir en format standard"""
        
        location = data.get('location', {})
        current = data.get('current', {})
        pollution = current.get('pollution', {})
        weather = current.get('weather', {})
        
        return {
            'name': f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}",
            'coordinates': [target_lat, target_lon],
            'aqi': pollution.get('aqius', 50),  # US AQI
            'pm25': pollution.get('p2', {}).get('conc', 0),  # Concentration PM2.5
            'pm10': pollution.get('p1', {}).get('conc', 0),  # Concentration PM10
            'no2': 15.0,  # IQAir ne fournit que PM, estimation
            'o3': 50.0,   # Estimation
            'so2': 5.0,   # Estimation
            'co': 1.0,    # Estimation
            'temperature': weather.get('tp', 20),
            'humidity': weather.get('hu', 50),
            'pressure': weather.get('pr', 1013),
            'wind_speed': weather.get('ws', 0),
            'data_source': 'IQAir Real Data',
            'timestamp': pollution.get('ts', ''),
            'data_quality': 'premium',
            'coverage': 'worldwide'
        }
    
    # ==========================================
    # MÉTHODES UTILITAIRES
    # ==========================================
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcule la distance en kilomètres entre deux points (formule haversine)"""
        R = 6371  # Rayon de la Terre en km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_aqi_from_pollutants(self, pollutants: Dict[str, float]) -> int:
        """Calcule l'AQI basé sur les polluants disponibles"""
        aqi_values = []
        
        # PM2.5
        if 'pm25' in pollutants or 'pm2.5' in pollutants:
            pm25 = pollutants.get('pm25', pollutants.get('pm2.5', 0))
            aqi_values.append(self._pm25_to_aqi(pm25))
        
        # PM10
        if 'pm10' in pollutants:
            aqi_values.append(self._pm10_to_aqi(pollutants['pm10']))
        
        # NO2
        if 'no2' in pollutants:
            aqi_values.append(self._no2_to_aqi(pollutants['no2']))
        
        # O3
        if 'o3' in pollutants:
            aqi_values.append(self._o3_to_aqi(pollutants['o3']))
        
        return max(aqi_values) if aqi_values else 50
    
    def _calculate_aqi_from_pm25(self, pm25: float) -> int:
        """Calcule l'AQI basé uniquement sur PM2.5"""
        return self._pm25_to_aqi(pm25)
    
    def _pm25_to_aqi(self, pm25: float) -> int:
        """Convertit PM2.5 en AQI selon standards EPA"""
        if pm25 <= 12.0:
            return int(pm25 * 50 / 12.0)
        elif pm25 <= 35.4:
            return int(50 + (pm25 - 12.0) * 50 / (35.4 - 12.0))
        elif pm25 <= 55.4:
            return int(100 + (pm25 - 35.4) * 50 / (55.4 - 35.4))
        elif pm25 <= 150.4:
            return int(150 + (pm25 - 55.4) * 50 / (150.4 - 55.4))
        elif pm25 <= 250.4:
            return int(200 + (pm25 - 150.4) * 100 / (250.4 - 150.4))
        else:
            return min(500, int(300 + (pm25 - 250.4) * 200 / (500.4 - 250.4)))
    
    def _pm10_to_aqi(self, pm10: float) -> int:
        """Convertit PM10 en AQI selon standards EPA"""
        if pm10 <= 54:
            return int(pm10 * 50 / 54)
        elif pm10 <= 154:
            return int(50 + (pm10 - 54) * 50 / (154 - 54))
        elif pm10 <= 254:
            return int(100 + (pm10 - 154) * 50 / (254 - 154))
        elif pm10 <= 354:
            return int(150 + (pm10 - 254) * 50 / (354 - 254))
        elif pm10 <= 424:
            return int(200 + (pm10 - 354) * 100 / (424 - 354))
        else:
            return min(500, int(300 + (pm10 - 424) * 200 / (604 - 424)))
    
    def _no2_to_aqi(self, no2: float) -> int:
        """Convertit NO2 (µg/m³) en AQI approximatif"""
        # Conversion approximative NO2 µg/m³ -> AQI
        if no2 <= 40:
            return int(no2 * 50 / 40)
        elif no2 <= 80:
            return int(50 + (no2 - 40) * 50 / 40)
        elif no2 <= 120:
            return int(100 + (no2 - 80) * 50 / 40)
        else:
            return min(200, int(150 + (no2 - 120) * 50 / 80))
    
    def _o3_to_aqi(self, o3: float) -> int:
        """Convertit O3 (µg/m³) en AQI approximatif"""
        # Conversion approximative O3 µg/m³ -> AQI
        if o3 <= 100:
            return int(o3 * 50 / 100)
        elif o3 <= 160:
            return int(50 + (o3 - 100) * 50 / 60)
        elif o3 <= 215:
            return int(100 + (o3 - 160) * 50 / 55)
        else:
            return min(200, int(150 + (o3 - 215) * 50 / 85))
    
    def _aqi_to_concentration(self, pollutant: str, aqi: int) -> float:
        """Convertit AQI vers concentration approximative"""
        if pollutant == 'pm25':
            if aqi <= 50:
                return aqi * 12.0 / 50
            elif aqi <= 100:
                return 12.0 + (aqi - 50) * (35.4 - 12.0) / 50
            else:
                return min(55.4, 35.4 + (aqi - 100) * (55.4 - 35.4) / 50)
        elif pollutant == 'pm10':
            if aqi <= 50:
                return aqi * 54 / 50
            elif aqi <= 100:
                return 54 + (aqi - 50) * (154 - 54) / 50
            else:
                return min(254, 154 + (aqi - 100) * (254 - 154) / 50)
        elif pollutant == 'o3':
            if aqi <= 50:
                return aqi * 100 / 50
            elif aqi <= 100:
                return 100 + (aqi - 50) * 60 / 50
            else:
                return min(215, 160 + (aqi - 100) * 55 / 50)
        else:
            return 15.0  # Valeur par défaut
    
    # ==========================================
    # MÉTHODE PRINCIPALE
    # ==========================================
    
    async def get_real_air_quality_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Récupère les données de qualité de l'air de VRAIES sources
        Cascade par ordre de priorité et de fiabilité
        """
        logger.info(f"🔍 Recherche de données réelles pour {latitude}, {longitude}")
        
        # Liste des sources par ordre de priorité
        sources = [
            ("OpenAQ v3", self.get_openaq_v3_data),
            ("PurpleAir", self.get_purpleair_data),
            ("AirNow EPA", self.get_airnow_data),
            ("IQAir", self.get_iqair_data),
        ]
        
        for source_name, source_method in sources:
            try:
                logger.info(f"📡 Tentative {source_name}...")
                data = await source_method(latitude, longitude)
                
                if data:
                    logger.info(f"✅ Données récupérées de {source_name}")
                    data['primary_source'] = source_name
                    return data
                else:
                    logger.warning(f"⚠️ {source_name}: Pas de données disponibles")
                    
            except Exception as e:
                logger.error(f"❌ Erreur {source_name}: {e}")
                continue
        
        logger.error("❌ AUCUNE source réelle n'a fourni de données")
        return None


# ==========================================
# SCRIPT DE TEST
# ==========================================

async def test_real_apis():
    """Test toutes les connexions API réelles"""
    print("🧪 TEST DES CONNEXIONS API RÉELLES")
    print("=" * 50)
    
    # Coordonnées de test
    test_locations = [
        (48.8566, 2.3522, "Paris"),
        (40.7128, -74.0060, "New York"),
        (34.0522, -118.2437, "Los Angeles"),
        (51.5074, -0.1278, "London")
    ]
    
    async with RealAPIConnector() as connector:
        for lat, lon, city in test_locations:
            print(f"\n📍 Test pour {city} ({lat}, {lon})")
            print("-" * 30)
            
            data = await connector.get_real_air_quality_data(lat, lon)
            
            if data:
                print(f"✅ Données récupérées de: {data.get('primary_source')}")
                print(f"   AQI: {data.get('aqi')}")
                print(f"   PM2.5: {data.get('pm25')} µg/m³")
                print(f"   Source: {data.get('data_source')}")
            else:
                print("❌ Aucune donnée réelle disponible")

if __name__ == "__main__":
    # Exemple d'utilisation
    asyncio.run(test_real_apis())
#!/usr/bin/env python3
"""
Collecteur de données air quality intégré avec toutes les APIs fonctionnelles.
"""
import aiohttp
import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class IntegratedAirQualityCollector:
    """Collecteur intégré pour données de qualité de l'air."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY")
        self.epa_key = os.getenv("EPA_API_KEY")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_comprehensive_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Récupère des données de toutes les sources disponibles."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': {'latitude': latitude, 'longitude': longitude},
            'sources': {}
        }
        
        # 1. OpenWeatherMap Air Pollution (Principal - fonctionne partout)
        if self.openweather_key:
            ow_data = await self._get_openweather_pollution(latitude, longitude)
            if ow_data:
                results['sources']['openweather'] = ow_data
                results['primary_aqi'] = ow_data.get('aqi')
                results['primary_source'] = 'OpenWeather'
        
        # 2. EPA AirNow (US seulement, si clé disponible)
        if self.epa_key and self._is_us_location(latitude, longitude):
            epa_data = await self._get_epa_data(latitude, longitude)
            if epa_data:
                results['sources']['epa'] = epa_data
                # Si pas d'AQI principal, utiliser EPA
                if not results.get('primary_aqi') and epa_data.get('measurements'):
                    first_measurement = epa_data['measurements'][0]
                    results['primary_aqi'] = first_measurement.get('aqi')
                    results['primary_source'] = 'EPA'
        
        # 3. OpenAQ v3 (Global, avec clé si disponible)
        openaq_data = await self._get_openaq_v3_data(latitude, longitude)
        if openaq_data:
            results['sources']['openaq'] = openaq_data
        
        # Si aucune source n'a fourni d'AQI, utiliser une valeur par défaut
        if not results.get('primary_aqi'):
            results['primary_aqi'] = 50
            results['primary_source'] = 'Default'
        
        return results
    
    async def _get_waqi_data(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Récupère les données WAQI."""
        try:
            # Essayer d'abord par coordonnées géographiques
            url = f"https://api.waqi.info/feed/geo:{latitude};{longitude}/?token=demo"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'ok' and 'data' in data:
                        waqi_info = data['data']
                        
                        # Vérifier que nous avons une station valide
                        if waqi_info.get('aqi', -1) > 0:
                            result = {
                                'aqi': waqi_info.get('aqi'),
                                'station_name': waqi_info.get('city', {}).get('name', 'Unknown'),
                                'measurement_time': waqi_info.get('time', {}).get('iso'),
                                'pollutants': {}
                            }
                            
                            # Polluants individuels
                            iaqi = waqi_info.get('iaqi', {})
                            for pollutant in ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2']:
                                if pollutant in iaqi:
                                    result['pollutants'][pollutant] = {
                                        'value': iaqi[pollutant].get('v'),
                                        'unit': 'µg/m³' if pollutant.startswith('pm') else 'ppb'
                                    }
                            
                            logger.info(f"WAQI data: AQI {result['aqi']} from {result['station_name']}")
                            return result
                    
                    # Si les coordonnées ne fonctionnent pas, essayer par ville proche
                    return await self._get_waqi_by_city(latitude, longitude)
                        
        except Exception as e:
            logger.error(f"Error fetching WAQI data: {e}")
            return await self._get_waqi_by_city(latitude, longitude)
    
    async def _get_waqi_by_city(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Récupère WAQI par ville la plus proche."""
        try:
            # Mapping des régions vers les villes WAQI
            city_mapping = {
                # Nord-Est US
                (40.7589, -73.9851): "newyork",  # New York
                (42.3601, -71.0589): "boston",   # Boston
                (38.9072, -77.0369): "washington", # Washington DC
                
                # Ouest US
                (34.0522, -118.2437): "losangeles", # Los Angeles
                (37.7749, -122.4194): "sanfrancisco", # San Francisco
                (47.6062, -122.3321): "seattle",     # Seattle
                
                # Europe
                (48.8566, 2.3522): "paris",      # Paris
                (51.5074, -0.1278): "london",    # Londres
                (52.5200, 13.4050): "berlin",    # Berlin
                
                # Asie
                (35.6762, 139.6503): "tokyo",    # Tokyo
                (39.9042, 116.4074): "beijing",  # Beijing
                (31.2304, 121.4737): "shanghai"  # Shanghai
            }
            
            # Trouver la ville la plus proche
            best_city = "newyork"  # défaut
            min_distance = float('inf')
            
            for (city_lat, city_lon), city_name in city_mapping.items():
                distance = ((latitude - city_lat) ** 2 + (longitude - city_lon) ** 2) ** 0.5
                if distance < min_distance:
                    min_distance = distance
                    best_city = city_name
            
            url = f"https://api.waqi.info/feed/{best_city}/?token=demo"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'ok' and 'data' in data:
                        waqi_info = data['data']
                        
                        result = {
                            'aqi': waqi_info.get('aqi'),
                            'station_name': f"{waqi_info.get('city', {}).get('name', best_city)} (closest)",
                            'measurement_time': waqi_info.get('time', {}).get('iso'),
                            'pollutants': {}
                        }
                        
                        # Polluants individuels
                        iaqi = waqi_info.get('iaqi', {})
                        for pollutant in ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2']:
                            if pollutant in iaqi:
                                result['pollutants'][pollutant] = {
                                    'value': iaqi[pollutant].get('v'),
                                    'unit': 'µg/m³' if pollutant.startswith('pm') else 'ppb'
                                }
                        
                        logger.info(f"WAQI data (closest city): AQI {result['aqi']} from {result['station_name']}")
                        return result
                        
        except Exception as e:
            logger.error(f"Error fetching WAQI by city: {e}")
            return None
    
    async def _get_openweather_pollution(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Récupère les données de pollution OpenWeatherMap."""
        try:
            url = "http://api.openweathermap.org/data/2.5/air_pollution"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.openweather_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'list' in data and data['list']:
                        pollution_data = data['list'][0]
                        components = pollution_data.get('components', {})
                        
                        result = {
                            'aqi': pollution_data.get('main', {}).get('aqi'),
                            'measurement_time': datetime.fromtimestamp(pollution_data.get('dt', 0)).isoformat(),
                            'pollutants': {}
                        }
                        
                        # Convertir les composants OpenWeather avec valeurs réelles
                        component_mapping = {
                            'co': ('co', 'µg/m³'),
                            'no': ('no', 'µg/m³'),
                            'no2': ('no2', 'µg/m³'),
                            'o3': ('o3', 'µg/m³'),
                            'so2': ('so2', 'µg/m³'),
                            'pm2_5': ('pm25', 'µg/m³'),
                            'pm10': ('pm10', 'µg/m³'),
                            'nh3': ('nh3', 'µg/m³')
                        }
                        
                        for ow_name, (our_name, unit) in component_mapping.items():
                            if ow_name in components:
                                result['pollutants'][our_name] = {
                                    'value': components[ow_name],
                                    'unit': unit
                                }
                        
                        logger.info(f"OpenWeather pollution data: AQI {result['aqi']}, {len(result['pollutants'])} pollutants")
                        return result
                else:
                    logger.error(f"OpenWeather API error: {response.status}")
                    return None
                        
        except Exception as e:
            logger.error(f"Error fetching OpenWeather pollution data: {e}")
            return None
    
    async def _get_openaq_v3_data(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Récupère les données OpenAQ v3."""
        try:
            # Rechercher les stations proches
            url = "https://api.openaq.org/v3/locations"
            params = {
                'coordinates': f"{latitude},{longitude}",
                'radius': 25000,  # 25km
                'limit': 5
            }
            
            headers = {}
            openaq_key = os.getenv("OPENAQ_API_KEY")
            if openaq_key and openaq_key != "your_openaq_key":
                headers['X-API-Key'] = openaq_key
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    locations = data.get('results', [])
                    
                    if locations:
                        # Prendre la première station
                        location = locations[0]
                        location_id = location.get('id')
                        
                        # Récupérer les mesures récentes
                        measurements_url = "https://api.openaq.org/v3/measurements"
                        measurements_params = {
                            'locations_id': location_id,
                            'limit': 10,
                            'order_by': 'datetime',
                            'sort_order': 'desc'
                        }
                        
                        async with self.session.get(measurements_url, params=measurements_params, headers=headers) as meas_response:
                            if meas_response.status == 200:
                                meas_data = await meas_response.json()
                                measurements = meas_data.get('results', [])
                                
                                if measurements:
                                    result = {
                                        'station_name': location.get('name'),
                                        'station_id': location_id,
                                        'pollutants': {}
                                    }
                                    
                                    # Organiser par polluant
                                    for measurement in measurements:
                                        parameter = measurement.get('parameter', {}).get('name')
                                        if parameter:
                                            result['pollutants'][parameter.lower()] = {
                                                'value': measurement.get('value'),
                                                'unit': measurement.get('parameter', {}).get('units'),
                                                'datetime': measurement.get('date', {}).get('utc')
                                            }
                                    
                                    logger.info(f"OpenAQ v3 data: {len(result['pollutants'])} pollutants from {result['station_name']}")
                                    return result
                                    
        except Exception as e:
            logger.error(f"Error fetching OpenAQ v3 data: {e}")
            return None
    
    async def _get_epa_data(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Récupère les données EPA AirNow."""
        try:
            # Convertir en zip code approximatif pour EPA
            # Pour l'instant, utiliser les coordonnées directement
            url = "https://www.airnowapi.org/aq/observation/latLong/current/"
            params = {
                'format': 'application/json',
                'latitude': latitude,
                'longitude': longitude,
                'distance': 25,
                'API_KEY': self.epa_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        result = {
                            'measurements': [],
                            'station_count': len(data)
                        }
                        
                        for measurement in data:
                            result['measurements'].append({
                                'parameter': measurement.get('ParameterName'),
                                'aqi': measurement.get('AQI'),
                                'value': measurement.get('Value'),
                                'unit': measurement.get('Unit'),
                                'category': measurement.get('Category', {}).get('Name'),
                                'site_name': measurement.get('SiteName'),
                                'datetime': measurement.get('DateObserved')
                            })
                        
                        logger.info(f"EPA data: {len(data)} measurements")
                        return result
                        
        except Exception as e:
            logger.error(f"Error fetching EPA data: {e}")
            return None
    
    def _is_us_location(self, latitude: float, longitude: float) -> bool:
        """Vérifie si les coordonnées sont aux États-Unis."""
        # Approximation grossière des frontières US
        return (24.0 <= latitude <= 71.0) and (-179.0 <= longitude <= -66.0)
    
    def _calculate_combined_aqi(self, sources_data: Dict[str, Any]) -> int:
        """Calcule un AQI combiné à partir de plusieurs sources."""
        aqi_values = []
        
        for source_name, source_data in sources_data.items():
            if 'aqi' in source_data and source_data['aqi']:
                aqi_values.append(source_data['aqi'])
        
        if aqi_values:
            # Prendre la médiane pour éviter les valeurs aberrantes
            aqi_values.sort()
            n = len(aqi_values)
            if n % 2 == 0:
                return int((aqi_values[n//2-1] + aqi_values[n//2]) / 2)
            else:
                return aqi_values[n//2]
        
        return 50  # Valeur par défaut


# Instance globale
integrated_collector = IntegratedAirQualityCollector()
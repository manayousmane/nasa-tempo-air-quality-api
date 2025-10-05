#!/usr/bin/env python3
"""
Collecteur de données air quality simplifié avec les APIs fonctionnelles uniquement.
"""
import aiohttp
import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimplifiedAirQualityCollector:
    """Collecteur simplifié pour données de qualité de l'air - APIs fonctionnelles seulement."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY", "ddd984279653ed94a82f3c9d667fa03f")
        self.epa_key = os.getenv("EPA_API_KEY")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_air_quality_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Récupère des données de qualité de l'air des sources fiables."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': {'latitude': latitude, 'longitude': longitude},
            'sources': {},
            'primary_aqi': None,
            'primary_source': None
        }
        
        # 1. OpenWeatherMap Air Pollution (Principal - fonctionne mondialement)
        if self.openweather_key:
            ow_data = await self._get_openweather_pollution(latitude, longitude)
            if ow_data:
                results['sources']['openweather'] = ow_data
                results['primary_aqi'] = ow_data.get('aqi')
                results['primary_source'] = 'OpenWeather'
                logger.info(f"OpenWeatherMap data obtained: AQI {ow_data.get('aqi')}")
        
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
                logger.info(f"EPA data obtained: {len(epa_data.get('measurements', []))} measurements")
        
        # Si aucune source n'a fourni d'AQI, utiliser une estimation
        if not results.get('primary_aqi'):
            results['primary_aqi'] = 50  # Valeur neutre
            results['primary_source'] = 'Default'
            logger.warning(f"No AQI data available for {latitude}, {longitude} - using default")
        
        return results
    
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
                        
                        # Convertir l'AQI OpenWeather (1-5) vers AQI US (0-500)
                        ow_aqi = pollution_data.get('main', {}).get('aqi', 3)
                        aqi_conversion = {1: 25, 2: 60, 3: 100, 4: 175, 5: 350}
                        us_aqi = aqi_conversion.get(ow_aqi, 100)
                        
                        result = {
                            'aqi': us_aqi,
                            'aqi_category': self._get_aqi_category(us_aqi),
                            'openweather_aqi': ow_aqi,
                            'measurement_time': datetime.fromtimestamp(pollution_data.get('dt', 0)).isoformat(),
                            'pollutants': {}
                        }
                        
                        # Composants détaillés
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
                        
                        return result
                else:
                    logger.error(f"OpenWeather API error: {response.status}")
                    return None
                        
        except Exception as e:
            logger.error(f"Error fetching OpenWeather pollution data: {e}")
            return None
    
    async def _get_epa_data(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Récupère les données EPA AirNow (US seulement)."""
        try:
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
                        
                        return result
                else:
                    logger.error(f"EPA API error: {response.status}")
                    return None
                        
        except Exception as e:
            logger.error(f"Error fetching EPA data: {e}")
            return None
    
    def _is_us_location(self, latitude: float, longitude: float) -> bool:
        """Vérifie si les coordonnées sont aux États-Unis."""
        # Frontières approximatives des États-Unis
        return (24.0 <= latitude <= 71.0) and (-179.0 <= longitude <= -66.0)
    
    def _get_aqi_category(self, aqi: int) -> str:
        """Obtient la catégorie AQI selon les standards EPA."""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"


# Instance globale
simplified_collector = SimplifiedAirQualityCollector()
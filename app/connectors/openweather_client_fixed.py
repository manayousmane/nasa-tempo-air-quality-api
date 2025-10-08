"""
Client OpenWeather - Version corrigée
"""
import aiohttp
import os
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class OpenWeatherClient:
    """Client spécialisé pour les données météo OpenWeather"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        logger.info(f"🌤️ OpenWeatherClient initialisé - API Key: {'✅' if self.api_key else '❌'}")
    
    async def get_weather_data(self, lat: float, lon: float) -> Optional[Dict]:
        """Récupère les données météo complètes depuis OpenWeather"""
        if not self.api_key:
            logger.error("❌ Clé OpenWeather manquante")
            return self._get_fallback_weather(lat, lon)
            
        try:
            async with aiohttp.ClientSession() as session:
                # Données météo actuelles
                weather_url = f"{self.base_url}/weather"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.api_key,
                    'units': 'metric',
                    'lang': 'fr'
                }
                
                async with session.get(weather_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = self._process_weather_data(data)
                        logger.info("✅ Données météo OpenWeather récupérées")
                        return result
                    else:
                        logger.error(f"❌ Erreur OpenWeather: {response.status}")
                        return self._get_fallback_weather(lat, lon)
                        
        except Exception as e:
            logger.error(f"❌ Erreur récupération météo: {e}")
            return self._get_fallback_weather(lat, lon)
    
    def _process_weather_data(self, data: Dict) -> Dict:
        """Traite les données météo OpenWeather"""
        main = data.get('main', {})
        wind = data.get('wind', {})
        weather = data.get('weather', [{}])[0]
        
        return {
            'temperature': main.get('temp', 15.0),
            'humidity': main.get('humidity', 65.0),
            'pressure': main.get('pressure', 1013.0),
            'wind_speed': wind.get('speed', 3.0),
            'wind_direction': self._degrees_to_direction(wind.get('deg')),
            'weather_condition': weather.get('description', 'clear'),
            'visibility': data.get('visibility', 10000) / 1000,  # Convertir en km
            'source': 'OpenWeather',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _get_fallback_weather(self, lat: float, lon: float) -> Dict:
        """Données météo de fallback"""
        return {
            'temperature': 15.0,
            'humidity': 65.0,
            'pressure': 1013.0,
            'wind_speed': 3.0,
            'wind_direction': 'N',
            'weather_condition': 'clear',
            'visibility': 10.0,
            'source': 'Fallback',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _degrees_to_direction(self, degrees: float) -> str:
        """Convertit les degrés en direction cardinale"""
        if degrees is None:
            return 'N'
            
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
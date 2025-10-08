# openweather_client.py
import aiohttp
import os
from datetime import datetime
import logging
from typing import Dict, Optional

# Chargement des variables d'environnement
from dotenv import load_dotenv
# Chercher le fichier .env dans le répertoire racine du projet
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class OpenWeatherClient:
    """Client spécialisé pour les données météo OpenWeather"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Log pour vérifier la clé API
        if self.api_key:
            logger.info(f"🌤️ OpenWeatherClient initialisé - API Key: ✅")
        else:
            logger.info(f"🌤️ OpenWeatherClient initialisé - API Key: ❌")
    
    async def get_weather_data(self, lat: float, lon: float) -> Optional[Dict]:
        """Récupère les données météo complètes depuis OpenWeather"""
        if not self.api_key:
            logger.error("❌ Clé OpenWeather manquante")
            return None
            
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
                        return self._process_weather_data(data)
                    else:
                        logger.error(f"❌ Erreur OpenWeather: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erreur récupération météo: {e}")
            return None
    
    def _process_weather_data(self, data: Dict) -> Dict:
        """Traite les données météo OpenWeather"""
        main = data.get('main', {})
        wind = data.get('wind', {})
        weather = data.get('weather', [{}])[0]
        
        return {
            'temperature': main.get('temp'),
            'humidity': main.get('humidity'),
            'pressure': main.get('pressure'),
            'wind_speed': wind.get('speed'),
            'wind_direction': self._degrees_to_direction(wind.get('deg')),
            'weather_condition': weather.get('description', ''),
            'visibility': data.get('visibility'),
            'source': 'OpenWeather',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _degrees_to_direction(self, degrees: float) -> str:
        """Convertit les degrés en direction cardinale"""
        if degrees is None:
            return 'N/A'
            
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
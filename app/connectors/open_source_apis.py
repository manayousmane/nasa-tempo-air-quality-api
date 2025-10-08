"""
Connecteurs pour APIs Open Source de Qualité de l'Air
Intègre: OpenAQ, AirNow, WAQI, AirVisual, PurpleAir
"""
import aiohttp
import os
from datetime import datetime
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Chargement des variables d'environnement
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class OpenSourceAPICollector:
    """Collecteur pour toutes les APIs open source de qualité de l'air"""
    
    def __init__(self):
        # APIs gratuites (sans clé requise)
        self.openaq_base = "https://api.openaq.org/v2"
        self.waqi_base = "https://api.waqi.info/feed"
        
        # APIs avec clé optionnelle
        self.airnow_key = os.getenv('AIRNOW_API_KEY')
        self.waqi_token = os.getenv('WAQI_TOKEN', 'demo')  # 'demo' token gratuit
        
        logger.info("🌍 Collecteur APIs Open Source initialisé")
        
    async def get_all_available_data(self, lat: float, lon: float) -> Dict:
        """Collecte depuis toutes les APIs disponibles et retourne la meilleure source"""
        sources_data = {}
        
        # 1. OpenAQ (API gratuite, très fiable)
        openaq_data = await self._get_openaq_data(lat, lon)
        if openaq_data:
            sources_data['openaq'] = openaq_data
            logger.info("✅ Données OpenAQ récupérées")
        
        # 2. World Air Quality Index (WAQI)
        waqi_data = await self._get_waqi_data(lat, lon)
        if waqi_data:
            sources_data['waqi'] = waqi_data
            logger.info("✅ Données WAQI récupérées")
        
        # 3. AirNow (si clé disponible)
        if self.airnow_key:
            airnow_data = await self._get_airnow_data(lat, lon)
            if airnow_data:
                sources_data['airnow'] = airnow_data
                logger.info("✅ Données AirNow récupérées")
        
        # 4. Combiner les meilleures données
        return self._combine_best_data(sources_data, lat, lon)
    
    async def _get_openaq_data(self, lat: float, lon: float) -> Optional[Dict]:
        """Récupère les données depuis OpenAQ (API gratuite)"""
        try:
            async with aiohttp.ClientSession() as session:
                # Chercher les stations proches
                url = f"{self.openaq_base}/latest"
                params = {
                    'coordinates': f"{lat},{lon}",
                    'radius': 25000,  # 25km radius
                    'limit': 100,
                    'sort': 'distance'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_openaq_data(data.get('results', []))
                    else:
                        logger.warning(f"⚠️ OpenAQ erreur {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erreur OpenAQ: {e}")
            return None
    
    async def _get_waqi_data(self, lat: float, lon: float) -> Optional[Dict]:
        """Récupère les données depuis World Air Quality Index"""
        try:
            async with aiohttp.ClientSession() as session:
                # WAQI par géolocalisation
                url = f"{self.waqi_base}/geo:{lat};{lon}/"
                params = {'token': self.waqi_token}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'ok':
                            return self._format_waqi_data(data.get('data', {}))
                    
                logger.warning(f"⚠️ WAQI erreur ou pas de données")
                return None
                        
        except Exception as e:
            logger.error(f"❌ Erreur WAQI: {e}")
            return None
    
    async def _get_airnow_data(self, lat: float, lon: float) -> Optional[Dict]:
        """Récupère les données depuis AirNow (EPA)"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.airnowapi.org/aq/observation/latLong/current/"
                params = {
                    'format': 'application/json',
                    'latitude': lat,
                    'longitude': lon,
                    'distance': 25,
                    'API_KEY': self.airnow_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_airnow_data(data)
                    else:
                        logger.warning(f"⚠️ AirNow erreur {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erreur AirNow: {e}")
            return None
    
    def _format_openaq_data(self, measurements: List[Dict]) -> Dict:
        """Formate les données OpenAQ"""
        if not measurements:
            return {}
        
        # Grouper par polluant
        pollutants = {}
        for measurement in measurements:
            param = measurement.get('parameter', '').lower()
            value = measurement.get('value')
            
            if param in ['pm25', 'pm2.5']:
                pollutants['pm25'] = value
            elif param in ['pm10']:
                pollutants['pm10'] = value
            elif param in ['no2']:
                pollutants['no2'] = value
            elif param in ['o3', 'ozone']:
                pollutants['o3'] = value
            elif param in ['so2']:
                pollutants['so2'] = value
            elif param in ['co']:
                pollutants['co'] = value
        
        if pollutants:
            pollutants.update({
                'source': 'OpenAQ',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'data_quality': 'high'
            })
        
        return pollutants
    
    def _format_waqi_data(self, data: Dict) -> Dict:
        """Formate les données WAQI"""
        if not data:
            return {}
        
        iaqi = data.get('iaqi', {})
        pollutants = {}
        
        # Extraire les polluants
        if 'pm25' in iaqi:
            pollutants['pm25'] = iaqi['pm25'].get('v')
        if 'pm10' in iaqi:
            pollutants['pm10'] = iaqi['pm10'].get('v')
        if 'no2' in iaqi:
            pollutants['no2'] = iaqi['no2'].get('v')
        if 'o3' in iaqi:
            pollutants['o3'] = iaqi['o3'].get('v')
        if 'so2' in iaqi:
            pollutants['so2'] = iaqi['so2'].get('v')
        if 'co' in iaqi:
            pollutants['co'] = iaqi['co'].get('v')
        
        if pollutants:
            pollutants.update({
                'aqi': data.get('aqi'),
                'source': 'WAQI',
                'station': data.get('city', {}).get('name', 'Unknown'),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'data_quality': 'medium'
            })
        
        return pollutants
    
    def _format_airnow_data(self, data: List[Dict]) -> Dict:
        """Formate les données AirNow"""
        if not data:
            return {}
        
        pollutants = {}
        
        for measurement in data:
            param = measurement.get('ParameterName', '').lower()
            value = measurement.get('Value')
            aqi = measurement.get('AQI')
            
            if 'pm2.5' in param:
                pollutants['pm25'] = value
                pollutants['pm25_aqi'] = aqi
            elif 'pm10' in param:
                pollutants['pm10'] = value
                pollutants['pm10_aqi'] = aqi
            elif 'ozone' in param or 'o3' in param:
                pollutants['o3'] = value
                pollutants['o3_aqi'] = aqi
        
        if pollutants:
            pollutants.update({
                'source': 'AirNow EPA',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'data_quality': 'high'
            })
        
        return pollutants
    
    def _combine_best_data(self, sources_data: Dict, lat: float, lon: float) -> Dict:
        """Combine les données des différentes sources pour optimiser la qualité"""
        if not sources_data:
            logger.warning("⚠️ Aucune donnée des APIs open source")
            return {}
        
        # Priorité: AirNow > OpenAQ > WAQI
        priority_sources = ['airnow', 'openaq', 'waqi']
        
        combined = {
            'coordinates': [lat, lon],
            'sources_used': list(sources_data.keys()),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Prendre la meilleure valeur pour chaque polluant
        pollutants = ['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']
        
        for pollutant in pollutants:
            best_value = None
            best_source = None
            
            for source in priority_sources:
                if source in sources_data and pollutant in sources_data[source]:
                    best_value = sources_data[source][pollutant]
                    best_source = source
                    break
            
            if best_value is not None:
                combined[pollutant] = best_value
                combined[f'{pollutant}_source'] = best_source
        
        # AQI principal (priorité à AirNow/WAQI qui ont des AQI calculés)
        aqi_source = None
        if 'waqi' in sources_data and 'aqi' in sources_data['waqi']:
            combined['aqi'] = sources_data['waqi']['aqi']
            aqi_source = 'WAQI'
        elif 'airnow' in sources_data:
            # Calculer AQI depuis AirNow si disponible
            combined['aqi'] = self._calculate_aqi_from_pollutants(combined)
            aqi_source = 'Calculated from AirNow'
        else:
            # Calculer AQI depuis les polluants disponibles
            combined['aqi'] = self._calculate_aqi_from_pollutants(combined)
            aqi_source = 'Calculated'
        
        combined['aqi_source'] = aqi_source
        combined['data_source'] = 'Open Source APIs'
        
        logger.info(f"✅ Données combinées depuis: {', '.join(sources_data.keys())}")
        return combined
    
    def _calculate_aqi_from_pollutants(self, data: Dict) -> int:
        """Calcule un AQI simplifié depuis les polluants"""
        pm25 = data.get('pm25')
        pm10 = data.get('pm10')
        no2 = data.get('no2')
        o3 = data.get('o3')
        
        aqi_values = []
        
        # AQI PM2.5 (EPA standard)
        if pm25:
            if pm25 <= 12:
                aqi_pm25 = (50/12) * pm25
            elif pm25 <= 35.4:
                aqi_pm25 = 50 + ((100-50)/(35.4-12)) * (pm25-12)
            elif pm25 <= 55.4:
                aqi_pm25 = 100 + ((150-100)/(55.4-35.4)) * (pm25-35.4)
            else:
                aqi_pm25 = min(150 + ((200-150)/(150.4-55.4)) * (pm25-55.4), 300)
            aqi_values.append(aqi_pm25)
        
        # AQI NO2 (approximation)
        if no2:
            aqi_no2 = min((no2 / 100) * 100, 200)
            aqi_values.append(aqi_no2)
        
        # AQI O3 (approximation)
        if o3:
            aqi_o3 = min((o3 / 70) * 100, 200)
            aqi_values.append(aqi_o3)
        
        return int(max(aqi_values)) if aqi_values else 50
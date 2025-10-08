# air_quality_integration.py
import asyncio
import logging
from datetime import datetime
from typing import Dict
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from app.connectors.tempo_full_client import TempoFullClient
    from app.connectors.openweather_client import OpenWeatherClient
    from app.connectors.open_source_apis import OpenSourceAPICollector
except ImportError:
    # Fallback pour import direct
    from connectors.tempo_full_client import TempoFullClient
    from connectors.openweather_client import OpenWeatherClient
    from connectors.open_source_apis import OpenSourceAPICollector

logger = logging.getLogger(__name__)

class AirQualityIntegration:
    """Service d'intégration pour votre endpoint /location/full"""
    
    def __init__(self):
        self.tempo_client = TempoFullClient()
        self.weather_client = OpenWeatherClient()
        self.open_source_collector = OpenSourceAPICollector()
        
    async def get_real_time_data(self, lat: float, lon: float) -> Dict:
        """
        Récupère les données TEMPO + Météo pour /location/full
        Stratégie: TEMPO → APIs Open Source → OpenWeather → Fallback
        """
        final_data = {}
        
        # 1. TEMPO - Données satellites (priorité absolue)
        logger.info("🛰️ Récupération des données TEMPO...")
        tempo_data = await self.tempo_client.get_all_pollutants(lat, lon)
        
        if tempo_data:
            final_data.update(self._format_tempo_data(tempo_data))
            final_data['data_source'] = 'TEMPO'
            logger.info("✅ Données TEMPO intégrées")
        else:
            logger.warning("⚠️ Aucune donnée TEMPO disponible")
            final_data['data_source'] = 'Open Source APIs'
        
        # 2. APIs Open Source - Remplacement de la simulation
        if not tempo_data:
            logger.info("� Récupération depuis APIs Open Source...")
            open_source_data = await self.open_source_collector.get_all_available_data(lat, lon)
            
            if open_source_data:
                final_data.update(open_source_data)
                logger.info("✅ Données APIs Open Source intégrées")
            else:
                logger.warning("⚠️ APIs Open Source indisponibles, fallback simulation")
                # En dernier recours seulement
                simulated_data = await self._get_smart_simulation(lat, lon)
                final_data.update(simulated_data)
                final_data['data_source'] = 'Simulation (Fallback)'
        
        # 3. Météo - OpenWeather (toujours essayé)
        logger.info("�️ Récupération des données météo...")
        weather_data = await self.weather_client.get_weather_data(lat, lon)
        
        if weather_data:
            final_data.update(weather_data)
            logger.info("✅ Données météo intégrées")
        else:
            # Fallback météo basique
            final_data.update(self._get_basic_weather_fallback(lat, lon))
            logger.warning("⚠️ Fallback météo utilisé")
        
        # 4. Calcul AQI final (utilise l'AQI des APIs si disponible)
        if 'aqi' not in final_data:
            final_data['aqi'] = self._calculate_comprehensive_aqi(final_data)
        
        final_data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        
        return final_data
    
    def _format_tempo_data(self, tempo_data: Dict) -> Dict:
        """Formate les données TEMPO pour votre API"""
        formatted = {}
        
        # Mapping TEMPO → format de votre API
        mapping = {
            'no2': 'no2',
            'hcho': 'formaldehyde',  # Optionnel - à adapter
            'aerosol': 'pm10',       # Approximation aerosol → PM10
            'o3': 'o3'
        }
        
        for tempo_key, api_key in mapping.items():
            if tempo_key in tempo_data:
                formatted[api_key] = tempo_data[tempo_key]['value']
        
        return formatted
    
    async def _get_smart_simulation(self, lat: float, lon: float) -> Dict:
        """Simulation INTELLIGENTE seulement si TEMPO échoue"""
        logger.info("🎯 Génération de données simulées intelligentes")
        
        # Basé sur la localisation et l'heure
        is_urban = self._is_urban_area(lat, lon)
        current_hour = datetime.now().hour
        is_rush_hour = (7 <= current_hour <= 9) or (16 <= current_hour <= 19)
        
        if is_urban:
            base_pm25 = 18 + (5 if is_rush_hour else 0)
            base_no2 = 30 + (10 if is_rush_hour else 0)
            base_o3 = 45 - (10 if is_rush_hour else 0)  # O3 baisse en heure de pointe
        else:
            base_pm25 = 8
            base_no2 = 12
            base_o3 = 55
        
        # Variation réaliste
        import random
        variation = random.uniform(0.9, 1.1)
        
        return {
            'pm25': round(base_pm25 * variation, 1),
            'pm10': round(base_pm25 * 1.6 * variation, 1),
            'no2': round(base_no2 * variation, 1),
            'o3': round(base_o3 * variation, 1),
            'so2': round(4 * variation, 1),
            'co': round(0.7 * variation, 2),
            'simulation_note': 'Données simulées - TEMPO indisponible'
        }
    
    def _get_basic_weather_fallback(self, lat: float, lon: float) -> Dict:
        """Fallback météo basique"""
        return {
            'temperature': round(15 + (lat / 10), 1),
            'humidity': 65.0,
            'pressure': 1013.0,
            'wind_speed': 3.0,
            'wind_direction': 'N',
            'weather_condition': 'clear',
            'visibility': 10.0,
            'source': 'Fallback'
        }
    
    def _is_urban_area(self, lat: float, lon: float) -> bool:
        """Détecte les zones urbaines"""
        urban_areas = [
            (48.8566, 2.3522, 0.8),   # Paris
            (40.7128, -74.0060, 0.8),  # NYC
            (34.0522, -118.2437, 0.8), # LA
            (51.5074, -0.1278, 0.8),   # London
            (43.6532, -79.3832, 0.5),  # Toronto
        ]
        
        for city_lat, city_lon, radius in urban_areas:
            if abs(lat - city_lat) < radius and abs(lon - city_lon) < radius:
                return True
        return False
    
    def _calculate_comprehensive_aqi(self, data: Dict) -> int:
        """Calcule l'AQI basé sur les données disponibles"""
        # Utilise votre fonction existante ou une version adaptée
        pm25 = data.get('pm25', 10)
        pm10 = data.get('pm10', 20)
        no2 = data.get('no2', 15)
        o3 = data.get('o3', 40)
        
        # Calcul AQI simplifié
        aqi_pm25 = min((pm25 / 12.0) * 50, 150)
        aqi_no2 = min((no2 / 40.0) * 50, 150)
        
        return int(max(aqi_pm25, aqi_no2, 25))
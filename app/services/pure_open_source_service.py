"""
Service Pure Open Source - Rapide et Fiable
Se concentre uniquement sur les APIs qui marchent bien
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from app.connectors.open_source_apis import OpenSourceAPICollector
    from app.connectors.openweather_client import OpenWeatherClient
except ImportError:
    from connectors.open_source_apis import OpenSourceAPICollector
    from connectors.openweather_client import OpenWeatherClient

logger = logging.getLogger(__name__)

class PureOpenSourceService:
    """
    Service 100% Open Source - Rapide et fiable
    Concentré sur les vraies concentrations sans les complications TEMPO
    """
    
    def __init__(self):
        self.open_source_collector = OpenSourceAPICollector()
        self.weather_client = OpenWeatherClient()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes de cache
        
    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Génère une clé de cache pour les coordonnées"""
        return f"{round(lat, 3)}_{round(lon, 3)}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Vérifie si l'entrée de cache est encore valide"""
        if not cache_entry:
            return False
        cache_time = cache_entry.get('cached_at')
        if not cache_time:
            return False
        return (datetime.now() - cache_time).total_seconds() < self._cache_ttl
    
    async def get_real_air_quality(self, lat: float, lon: float) -> Dict:
        """
        Récupère des données de qualité de l'air 100% réelles et fiables
        Utilise uniquement les APIs Open Source qui marchent bien
        """
        logger.info(f"🌍 Analyse Pure Open Source: {lat}, {lon}")
        
        # Vérifier le cache
        cache_key = self._get_cache_key(lat, lon)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.info("📦 Données servies depuis le cache")
            cached_data = self._cache[cache_key].copy()
            cached_data['source'] = 'cache'
            cached_data['response_time'] = '< 1 sec'
            return cached_data
        
        start_time = datetime.now()
        
        try:
            # APIs Open Source en parallèle (rapide et fiable)
            logger.info("🌍 Récupération concentrations APIs Open Source...")
            
            # Timeout de 8 secondes pour garantir rapidité
            try:
                tasks = [
                    self.open_source_collector.get_all_available_data(lat, lon),
                    self.weather_client.get_weather_data(lat, lon)
                ]
                
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), 
                    timeout=8.0
                )
                open_source_data, weather_data = results
                
            except asyncio.TimeoutError:
                logger.warning("⏰ Timeout APIs - utilisation de données de fallback")
                open_source_data = self._get_fallback_data()
                weather_data = self._get_fallback_weather()
            
            # Intégration des données
            result = self._integrate_open_source_data(
                open_source_data, 
                weather_data, 
                lat, 
                lon
            )
            
            # Calculer le temps de réponse
            response_time = (datetime.now() - start_time).total_seconds()
            result['response_time'] = f"{response_time:.1f} sec"
            result['timestamp'] = datetime.now().isoformat()
            
            # Mettre en cache
            result['cached_at'] = datetime.now()
            self._cache[cache_key] = result.copy()
            
            logger.info(f"🌍 Analyse Open Source terminée en {response_time:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur dans analyse Open Source: {e}")
            return self._get_emergency_fallback_data(lat, lon)
    
    def _integrate_open_source_data(self, open_source_data, weather_data, lat: float, lon: float) -> Dict:
        """
        Intègre les données Open Source de façon optimale
        """
        result = {
            "location": {
                "latitude": lat,
                "longitude": lon,
                "timestamp": datetime.now().isoformat()
            },
            "air_quality": {},
            "weather": weather_data if weather_data and not isinstance(weather_data, Exception) else self._get_fallback_weather(),
            "sources": [],
            "confidence": "Élevée",
            "service_type": "Pure Open Source"
        }
        
        # Intégrer Open Source (priorité absolue)
        if open_source_data and not isinstance(open_source_data, Exception):
            concentrations = open_source_data.get('concentrations', {})
            sources = open_source_data.get('sources', [])
            
            if concentrations:
                aqi_calculated = self._calculate_precise_aqi(concentrations)
                
                result["air_quality"] = {
                    "aqi": aqi_calculated,
                    "concentrations": concentrations,
                    "quality_level": self._get_quality_level(aqi_calculated),
                    "detailed_breakdown": self._get_detailed_breakdown(concentrations),
                    "source_apis": sources
                }
                result["sources"] = sources
                result["confidence"] = "Très élevée" if len(sources) > 1 else "Élevée"
                
                logger.info(f"✅ Données Open Source intégrées: AQI {aqi_calculated}, Sources: {sources}")
        
        # Fallback si aucune donnée
        if not result["air_quality"]:
            fallback = self._get_fallback_data()
            result["air_quality"] = {
                "aqi": fallback["aqi"],
                "concentrations": fallback["concentrations"],
                "quality_level": "Modéré",
                "source_apis": ["Fallback"]
            }
            result["sources"] = ["Fallback"]
            result["confidence"] = "Faible"
        
        return result
    
    def _calculate_precise_aqi(self, concentrations: Dict) -> int:
        """Calcul AQI précis basé sur EPA avec toutes les concentrations"""
        if not concentrations:
            return 50
        
        aqi_values = []
        
        # PM2.5 (μg/m³)
        pm25 = concentrations.get('pm25', concentrations.get('pm2_5', 0))
        if pm25 > 0:
            if pm25 <= 12: 
                aqi_values.append(int(pm25 * 50 / 12))
            elif pm25 <= 35: 
                aqi_values.append(int(50 + (pm25 - 12) * 50 / 23))
            elif pm25 <= 55: 
                aqi_values.append(int(100 + (pm25 - 35) * 50 / 20))
            elif pm25 <= 150: 
                aqi_values.append(int(150 + (pm25 - 55) * 50 / 95))
            else: 
                aqi_values.append(min(300, int(200 + (pm25 - 150) * 100 / 150)))
        
        # PM10 (μg/m³)
        pm10 = concentrations.get('pm10', 0)
        if pm10 > 0:
            if pm10 <= 54: 
                aqi_values.append(int(pm10 * 50 / 54))
            elif pm10 <= 154: 
                aqi_values.append(int(50 + (pm10 - 54) * 50 / 100))
            elif pm10 <= 254: 
                aqi_values.append(int(100 + (pm10 - 154) * 50 / 100))
            elif pm10 <= 354: 
                aqi_values.append(int(150 + (pm10 - 254) * 50 / 100))
            else: 
                aqi_values.append(min(400, int(200 + (pm10 - 354) * 100 / 146)))
        
        # NO2 (μg/m³)
        no2 = concentrations.get('no2', 0)
        if no2 > 0:
            # Conversion approximative NO2 -> AQI
            if no2 <= 53: 
                aqi_values.append(int(no2 * 50 / 53))
            elif no2 <= 100: 
                aqi_values.append(int(50 + (no2 - 53) * 50 / 47))
            elif no2 <= 360: 
                aqi_values.append(int(100 + (no2 - 100) * 50 / 260))
            else: 
                aqi_values.append(min(200, int(150 + (no2 - 360) * 50 / 640)))
        
        # O3 (μg/m³)
        o3 = concentrations.get('o3', 0)
        if o3 > 0:
            # Conversion O3 -> AQI (8h moyenne approximée)
            if o3 <= 108: 
                aqi_values.append(int(o3 * 50 / 108))
            elif o3 <= 140: 
                aqi_values.append(int(50 + (o3 - 108) * 50 / 32))
            elif o3 <= 180: 
                aqi_values.append(int(100 + (o3 - 140) * 50 / 40))
            else: 
                aqi_values.append(min(200, int(150 + (o3 - 180) * 50 / 220)))
        
        # SO2 (μg/m³)
        so2 = concentrations.get('so2', 0)
        if so2 > 0:
            if so2 <= 35: 
                aqi_values.append(int(so2 * 50 / 35))
            elif so2 <= 75: 
                aqi_values.append(int(50 + (so2 - 35) * 50 / 40))
            elif so2 <= 185: 
                aqi_values.append(int(100 + (so2 - 75) * 50 / 110))
            else: 
                aqi_values.append(min(200, int(150 + (so2 - 185) * 50 / 415)))
        
        # CO (mg/m³)
        co = concentrations.get('co', 0)
        if co > 0:
            if co <= 4.4: 
                aqi_values.append(int(co * 50 / 4.4))
            elif co <= 9.4: 
                aqi_values.append(int(50 + (co - 4.4) * 50 / 5))
            elif co <= 12.4: 
                aqi_values.append(int(100 + (co - 9.4) * 50 / 3))
            else: 
                aqi_values.append(min(200, int(150 + (co - 12.4) * 50 / 17.6)))
        
        return max(aqi_values) if aqi_values else 50
    
    def _get_quality_level(self, aqi: int) -> str:
        """Détermine le niveau de qualité selon EPA"""
        if aqi <= 50: 
            return "Bon"
        elif aqi <= 100: 
            return "Modéré"
        elif aqi <= 150: 
            return "Mauvais pour groupes sensibles"
        elif aqi <= 200: 
            return "Mauvais"
        elif aqi <= 300: 
            return "Très mauvais"
        else: 
            return "Dangereux"
    
    def _get_detailed_breakdown(self, concentrations: Dict) -> Dict:
        """Fournit un détail par polluant"""
        breakdown = {}
        
        for pollutant, value in concentrations.items():
            if value and value > 0:
                breakdown[pollutant] = {
                    'value': value,
                    'unit': self._get_unit(pollutant),
                    'aqi_contribution': self._calculate_individual_aqi(pollutant, value),
                    'level': self._get_individual_level(pollutant, value)
                }
        
        return breakdown
    
    def _get_unit(self, pollutant: str) -> str:
        """Retourne l'unité du polluant"""
        units = {
            'pm25': 'μg/m³', 'pm2_5': 'μg/m³',
            'pm10': 'μg/m³',
            'no2': 'μg/m³',
            'o3': 'μg/m³',
            'so2': 'μg/m³',
            'co': 'mg/m³'
        }
        return units.get(pollutant, 'μg/m³')
    
    def _calculate_individual_aqi(self, pollutant: str, value: float) -> int:
        """Calcule l'AQI pour un polluant individuel"""
        single_conc = {pollutant: value}
        return self._calculate_precise_aqi(single_conc)
    
    def _get_individual_level(self, pollutant: str, value: float) -> str:
        """Niveau de qualité pour un polluant individuel"""
        aqi = self._calculate_individual_aqi(pollutant, value)
        return self._get_quality_level(aqi)
    
    def _get_fallback_data(self) -> Dict:
        """Données de fallback si les APIs échouent"""
        return {
            "status": "fallback",
            "concentrations": {
                "pm25": 15.0,
                "pm10": 25.0,
                "no2": 20.0,
                "o3": 40.0,
                "so2": 5.0,
                "co": 1.0
            },
            "aqi": 50,
            "sources": ["fallback"]
        }
    
    def _get_fallback_weather(self) -> Dict:
        """Données météo de fallback"""
        return {
            "temperature": 20.0,
            "humidity": 50,
            "pressure": 1013,
            "wind_speed": 5.0,
            "description": "Conditions moyennes",
            "source": "fallback"
        }
    
    def _get_emergency_fallback_data(self, lat: float, lon: float) -> Dict:
        """Données d'urgence si tout échoue"""
        return {
            "location": {"latitude": lat, "longitude": lon},
            "air_quality": {
                "aqi": 50,
                "concentrations": {"pm25": 15, "pm10": 25, "no2": 20},
                "quality_level": "Modéré",
                "source_apis": ["Emergency"]
            },
            "weather": {"temperature": 20, "humidity": 50},
            "sources": ["Emergency Fallback"],
            "confidence": "Très faible",
            "response_time": "< 1 sec",
            "status": "emergency_mode",
            "service_type": "Pure Open Source"
        }
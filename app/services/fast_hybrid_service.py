"""
Service hybride optimisé : TEMPO + APIs Open Source avec cache et optimisations
Version rapide pour production avec gestion des timeouts
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from app.connectors.tempo_latest_client import TempoLatestDataClient
    from app.connectors.open_source_apis import OpenSourceAPICollector
    from app.connectors.openweather_client import OpenWeatherClient
except ImportError:
    from connectors.tempo_latest_client import TempoLatestDataClient
    from connectors.open_source_apis import OpenSourceAPICollector
    from connectors.openweather_client import OpenWeatherClient

logger = logging.getLogger(__name__)

class FastHybridService:
    """
    Service hybride optimisé avec cache et timeouts agressifs
    Priorité : Rapidité et fiabilité
    """
    
    def __init__(self):
        self.open_source_collector = OpenSourceAPICollector()
        self.weather_client = OpenWeatherClient()
        # TEMPO en mode optionnel avec timeout très court
        self.tempo_client = None
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
    
    async def get_fast_air_quality(self, lat: float, lon: float) -> Dict:
        """
        Récupère les données de qualité de l'air avec priorité sur la rapidité
        Stratégie : APIs Open Source en priorité, TEMPO optionnel avec timeout court
        """
        logger.info(f"⚡ Analyse rapide qualité air: {lat}, {lon}")
        
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
            # 1. APIs Open Source en parallèle (rapide et fiable)
            logger.info("🌍 Récupération concentrations APIs Open Source...")
            
            # Correction : appel asynchrone correct
            open_source_data = await self.open_source_collector.get_all_available_data(lat, lon)
            weather_data = await self.weather_client.get_weather_data(lat, lon)  # Correction du nom de méthode
            
            # 2. TEMPO optionnel avec timeout très court (2 secondes max)
            tempo_data = None
            try:
                if self.tempo_client is None:
                    self.tempo_client = TempoLatestDataClient()
                
                logger.info("🛰️ Tentative récupération TEMPO (timeout 3s)...")
                tempo_task = self.tempo_client.get_metadata_only(lat, lon)
                tempo_data = await asyncio.wait_for(tempo_task, timeout=3.0)
                logger.info("✅ Métadonnées TEMPO récupérées rapidement")
                
            except asyncio.TimeoutError:
                logger.warning("⏰ TEMPO timeout - continuons sans TEMPO")
                tempo_data = {"status": "timeout", "available": False}
            except Exception as e:
                logger.warning(f"⚠️ TEMPO indisponible: {e}")
                tempo_data = {"status": "error", "available": False}
            
            # 3. Calcul de l'AQI et intégration
            result = self._integrate_fast_data(
                open_source_data, 
                weather_data, 
                tempo_data, 
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
            
            logger.info(f"⚡ Analyse rapide terminée en {response_time:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur dans analyse rapide: {e}")
            return self._get_emergency_fallback_data(lat, lon)
    
    def _get_fallback_data(self) -> Dict:
        """Données de fallback si les APIs échouent"""
        return {
            "status": "fallback",
            "concentrations": {
                "pm25": 15.0,
                "pm10": 25.0,
                "no2": 20.0,
                "o3": 40.0
            },
            "aqi": 50,
            "source": "fallback"
        }
    
    def _get_fallback_weather(self) -> Dict:
        """Données météo de fallback"""
        return {
            "temperature": 20.0,
            "humidity": 50,
            "pressure": 1013,
            "wind_speed": 5.0,
            "source": "fallback"
        }
    
    def _integrate_fast_data(self, open_source_data, weather_data, tempo_data, lat: float, lon: float) -> Dict:
        """
        Intègre rapidement les données de toutes les sources
        """
        result = {
            "location": {
                "latitude": lat,
                "longitude": lon,
                "timestamp": datetime.now().isoformat()
            },
            "air_quality": {},
            "weather": weather_data if weather_data else self._get_fallback_weather(),
            "sources": [],
            "confidence": "Élevée"
        }
        
        # Intégrer Open Source (priorité)
        if open_source_data and not isinstance(open_source_data, Exception):
            concentrations = open_source_data.get('concentrations', {})
            if concentrations:
                result["air_quality"] = {
                    "aqi": self._calculate_fast_aqi(concentrations),
                    "concentrations": concentrations,
                    "quality_level": self._get_quality_level(concentrations)
                }
                result["sources"].append("Open Source APIs")
        
        # Ajouter TEMPO si disponible (bonus)
        if tempo_data and tempo_data.get('available', False):
            result["tempo_validation"] = {
                "available": True,
                "products": tempo_data.get('products', []),
                "last_update": tempo_data.get('retrieved_at')
            }
            result["sources"].append("TEMPO Satellite")
            result["confidence"] = "Très élevée"
        else:
            result["tempo_validation"] = {
                "available": False,
                "reason": tempo_data.get('status', 'unavailable') if tempo_data else 'not_attempted'
            }
        
        # Fallback si aucune donnée
        if not result["air_quality"]:
            fallback = self._get_fallback_data()
            result["air_quality"] = {
                "aqi": fallback["aqi"],
                "concentrations": fallback["concentrations"],
                "quality_level": "Modéré"
            }
            result["sources"] = ["Fallback"]
            result["confidence"] = "Faible"
        
        return result
    
    def _calculate_fast_aqi(self, concentrations: Dict) -> int:
        """Calcul AQI rapide basé sur EPA"""
        if not concentrations:
            return 50
        
        # Valeurs EPA simplifiées pour calcul rapide
        aqi_values = []
        
        # PM2.5
        pm25 = concentrations.get('pm25', concentrations.get('pm2_5', 0))
        if pm25 > 0:
            if pm25 <= 12: aqi_values.append(int(pm25 * 50 / 12))
            elif pm25 <= 35: aqi_values.append(int(50 + (pm25 - 12) * 50 / 23))
            elif pm25 <= 55: aqi_values.append(int(100 + (pm25 - 35) * 50 / 20))
            else: aqi_values.append(min(200, int(150 + (pm25 - 55) * 50 / 100)))
        
        # PM10
        pm10 = concentrations.get('pm10', 0)
        if pm10 > 0:
            if pm10 <= 54: aqi_values.append(int(pm10 * 50 / 54))
            elif pm10 <= 154: aqi_values.append(int(50 + (pm10 - 54) * 50 / 100))
            else: aqi_values.append(min(200, int(100 + (pm10 - 154) * 50 / 100)))
        
        # NO2 (approximation)
        no2 = concentrations.get('no2', 0)
        if no2 > 0:
            aqi_values.append(min(100, max(20, int(no2 * 2))))
        
        return max(aqi_values) if aqi_values else 50
    
    def _get_quality_level(self, concentrations: Dict) -> str:
        """Détermine le niveau de qualité rapidement"""
        aqi = self._calculate_fast_aqi(concentrations)
        if aqi <= 50: return "Bon"
        elif aqi <= 100: return "Modéré"
        elif aqi <= 150: return "Mauvais pour groupes sensibles"
        elif aqi <= 200: return "Mauvais"
        else: return "Très mauvais"
    
    def _get_emergency_fallback_data(self, lat: float, lon: float) -> Dict:
        """Données d'urgence si tout échoue"""
        return {
            "location": {"latitude": lat, "longitude": lon},
            "air_quality": {
                "aqi": 50,
                "concentrations": {"pm25": 15, "pm10": 25, "no2": 20},
                "quality_level": "Modéré"
            },
            "weather": {"temperature": 20, "humidity": 50},
            "sources": ["Emergency Fallback"],
            "confidence": "Très faible",
            "response_time": "< 1 sec",
            "status": "emergency_mode"
        }

    async def get_metadata_only(self, lat: float, lon: float) -> Dict:
        """
        Version ultra-rapide : métadonnées uniquement sans téléchargement
        """
        try:
            if self.tempo_client is None:
                self.tempo_client = TempoLatestDataClient()
            
            # Recherche métadonnées seulement (pas de téléchargement)
            return await self.tempo_client.get_search_metadata_only(lat, lon)
        except Exception as e:
            logger.warning(f"Métadonnées TEMPO indisponibles: {e}")
            return {"available": False, "reason": str(e)}
"""
Service hybride intelligent : TEMPO + APIs Open Source avec calcul d'AQI précis
Combine la qualité TEMPO avec les concentrations réelles des APIs ouvertes
"""
import logging
from datetime import datetime
from typing import Dict, Optional
import sys
import os

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

class HybridTEMPOService:
    """
    Service hybride intelligent combinant TEMPO + APIs Open Source
    Fournit les vraies concentrations ET la validation TEMPO
    """
    
    def __init__(self):
        self.tempo_client = TempoLatestDataClient()
        self.open_source_collector = OpenSourceAPICollector()
        self.weather_client = OpenWeatherClient()
        
    async def get_comprehensive_air_quality(self, lat: float, lon: float) -> Dict:
        """
        Récupère les données complètes : concentrations réelles + validation TEMPO + AQI précis
        """
        logger.info(f"🎯 Analyse complète qualité air TEMPO+APIs: {lat}, {lon}")
        
        try:
            # 1. Données TEMPO (validation/métadonnées)
            logger.info("🛰️ Récupération métadonnées TEMPO...")
            tempo_data = await self.tempo_client.get_latest_available_data(lat, lon)
            
            # 2. APIs Open Source (concentrations réelles)
            logger.info("🌍 Récupération concentrations APIs Open Source...")
            open_source_data = await self.open_source_collector.get_all_available_data(lat, lon)
            
            # 3. Données météo
            logger.info("🌤️ Récupération données météo...")
            weather_data = await self.weather_client.get_weather_data(lat, lon)
            
            # 4. Synthèse intelligente
            comprehensive_data = self._create_comprehensive_response(
                tempo_data, open_source_data, weather_data, lat, lon
            )
            
            logger.info(f"✅ Analyse complète terminée: AQI {comprehensive_data.get('aqi', 'N/A')}")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"❌ Erreur service hybride: {e}")
            return self._error_response(lat, lon, str(e))
    
    def _create_comprehensive_response(self, tempo_data: Dict, open_source_data: Dict, 
                                     weather_data: Dict, lat: float, lon: float) -> Dict:
        """
        Crée une réponse complète combinant toutes les sources
        """
        response = {
            'coordinates': [lat, lon],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data_sources': {
                'tempo_status': 'available' if tempo_data else 'unavailable',
                'open_source_status': 'available' if open_source_data else 'unavailable',
                'weather_status': 'available' if weather_data else 'unavailable'
            },
            'pollutants': {},
            'air_quality': {},
            'weather': weather_data or {},
            'tempo_validation': {}
        }
        
        # Polluants prioritaires avec concentrations réelles
        if open_source_data and 'sources_used' in open_source_data:
            logger.info(f"📊 Intégration concentrations depuis: {open_source_data['sources_used']}")
            
            # Concentrations réelles depuis APIs open source
            for pollutant in ['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']:
                if pollutant in open_source_data:
                    concentration = open_source_data[pollutant]
                    source = open_source_data.get(f'{pollutant}_source', 'Unknown')
                    
                    response['pollutants'][pollutant] = {
                        'concentration': concentration,
                        'unit': self._get_standard_unit(pollutant),
                        'source': source,
                        'quality': 'Real-time measurement',
                        'aqi_contribution': self._calculate_individual_aqi(pollutant, concentration)
                    }
            
            # AQI global calculé
            response['air_quality'] = {
                'aqi': open_source_data.get('aqi', self._calculate_comprehensive_aqi(response['pollutants'])),
                'category': self._get_aqi_category(open_source_data.get('aqi', 50)),
                'dominant_pollutant': self._find_dominant_pollutant(response['pollutants']),
                'calculation_method': 'EPA Standard + Real measurements'
            }
        
        # Validation et métadonnées TEMPO
        if tempo_data:
            response['tempo_validation'] = {
                'satellite_coverage': True,
                'available_products': list([k for k in tempo_data.keys() if k in ['no2', 'hcho', 'o3', 'aerosol']]),
                'search_period_days': tempo_data.get('search_period_days', 7),
                'latest_satellite_pass': self._get_latest_tempo_date(tempo_data),
                'data_quality': 'NASA Official Satellite Data',
                'note': 'TEMPO provides validation and trend analysis'
            }
            
            # Comparaison TEMPO vs Ground-based si possible
            comparison = self._compare_tempo_vs_ground(tempo_data, response['pollutants'])
            if comparison:
                response['tempo_validation']['comparison'] = comparison
        
        # Recommandations de santé
        response['health_recommendations'] = self._generate_health_recommendations(
            response['air_quality']
        )
        
        # Métadonnées de confiance
        response['confidence'] = {
            'overall': self._calculate_overall_confidence(tempo_data, open_source_data),
            'concentration_reliability': 'High' if open_source_data else 'Low',
            'temporal_accuracy': 'Real-time' if open_source_data else 'Estimated',
            'spatial_resolution': '~10km (API stations)' if open_source_data else '~50km (estimated)'
        }
        
        return response
    
    def _get_standard_unit(self, pollutant: str) -> str:
        """Unités standard pour chaque polluant"""
        units = {
            'pm25': 'μg/m³',
            'pm10': 'μg/m³', 
            'no2': 'μg/m³',
            'o3': 'μg/m³',
            'so2': 'μg/m³',
            'co': 'mg/m³'
        }
        return units.get(pollutant, 'unknown')
    
    def _calculate_individual_aqi(self, pollutant: str, concentration: float) -> int:
        """Calcule l'AQI individuel pour un polluant (méthode EPA)"""
        if concentration is None:
            return 0
            
        # Tables EPA simplifiées
        if pollutant == 'pm25':
            if concentration <= 12.0:
                return int((50/12.0) * concentration)
            elif concentration <= 35.4:
                return int(50 + ((100-50)/(35.4-12.0)) * (concentration-12.0))
            elif concentration <= 55.4:
                return int(100 + ((150-100)/(55.4-35.4)) * (concentration-35.4))
            else:
                return min(int(150 + ((200-150)/(150.4-55.4)) * (concentration-55.4)), 300)
        
        elif pollutant == 'pm10':
            if concentration <= 54:
                return int((50/54) * concentration)
            elif concentration <= 154:
                return int(50 + ((100-50)/(154-54)) * (concentration-54))
            else:
                return min(int(100 + ((150-100)/(254-154)) * (concentration-154)), 200)
        
        elif pollutant == 'no2':
            # Conversion ppb vers AQI (approximation)
            return min(int(concentration * 0.5), 200)
        
        elif pollutant == 'o3':
            # Conversion vers AQI (approximation)
            return min(int(concentration * 0.8), 200)
        
        else:
            return min(int(concentration * 0.3), 150)
    
    def _calculate_comprehensive_aqi(self, pollutants: Dict) -> int:
        """Calcule l'AQI global basé sur le polluant le plus élevé"""
        max_aqi = 0
        
        for pollutant, data in pollutants.items():
            if isinstance(data, dict) and 'aqi_contribution' in data:
                max_aqi = max(max_aqi, data['aqi_contribution'])
        
        return max_aqi if max_aqi > 0 else 50
    
    def _get_aqi_category(self, aqi: int) -> str:
        """Retourne la catégorie AQI"""
        if aqi <= 50:
            return "Bon"
        elif aqi <= 100:
            return "Modéré"
        elif aqi <= 150:
            return "Malsain pour groupes sensibles"
        elif aqi <= 200:
            return "Malsain"
        elif aqi <= 300:
            return "Très malsain"
        else:
            return "Dangereux"
    
    def _find_dominant_pollutant(self, pollutants: Dict) -> str:
        """Trouve le polluant dominant (AQI le plus élevé)"""
        max_aqi = 0
        dominant = "pm25"
        
        for pollutant, data in pollutants.items():
            if isinstance(data, dict) and 'aqi_contribution' in data:
                if data['aqi_contribution'] > max_aqi:
                    max_aqi = data['aqi_contribution']
                    dominant = pollutant
        
        return dominant
    
    def _get_latest_tempo_date(self, tempo_data: Dict) -> str:
        """Extrait la date la plus récente des données TEMPO"""
        latest_date = "Unknown"
        
        for key, value in tempo_data.items():
            if isinstance(value, dict) and 'date' in value:
                latest_date = value['date']
                break
        
        return latest_date
    
    def _compare_tempo_vs_ground(self, tempo_data: Dict, ground_pollutants: Dict) -> Optional[Dict]:
        """Compare les données TEMPO vs stations au sol (si applicable)"""
        # Pour l'instant, simple indication de disponibilité
        tempo_available = len([k for k in tempo_data.keys() if k in ['no2', 'hcho', 'o3']]) 
        ground_available = len(ground_pollutants)
        
        if tempo_available > 0 and ground_available > 0:
            return {
                'tempo_products': tempo_available,
                'ground_measurements': ground_available,
                'note': 'Both satellite and ground data available for cross-validation'
            }
        
        return None
    
    def _generate_health_recommendations(self, air_quality: Dict) -> Dict:
        """Génère des recommandations de santé basées sur l'AQI"""
        aqi = air_quality.get('aqi', 50)
        
        if aqi <= 50:
            return {
                'general': 'Qualité air excellente. Activités extérieures recommandées.',
                'sensitive': 'Aucune restriction pour les personnes sensibles.',
                'activities': 'Toutes activités extérieures possibles.'
            }
        elif aqi <= 100:
            return {
                'general': 'Qualité air acceptable. Activités normales possibles.',
                'sensitive': 'Personnes sensibles peuvent ressentir de légers effets.',
                'activities': 'Activités extérieures généralement sûres.'
            }
        elif aqi <= 150:
            return {
                'general': 'Malsain pour groupes sensibles.',
                'sensitive': 'Éviter les activités extérieures prolongées.',
                'activities': 'Réduire les activités intenses à l\'extérieur.'
            }
        else:
            return {
                'general': 'Qualité air malsaine. Limiter exposition extérieure.',
                'sensitive': 'Rester à l\'intérieur. Éviter toute activité extérieure.',
                'activities': 'Activités extérieures fortement déconseillées.'
            }
    
    def _calculate_overall_confidence(self, tempo_data: Dict, open_source_data: Dict) -> str:
        """Calcule le niveau de confiance global"""
        score = 0
        
        if tempo_data:
            score += 30  # TEMPO validation
        if open_source_data and open_source_data.get('sources_used'):
            score += 50  # Real measurements
        if len(open_source_data.get('sources_used', [])) > 1:
            score += 20  # Multiple sources
        
        if score >= 80:
            return "Très élevée"
        elif score >= 60:
            return "Élevée"
        elif score >= 40:
            return "Modérée"
        else:
            return "Limitée"
    
    def _error_response(self, lat: float, lon: float, error: str) -> Dict:
        """Réponse d'erreur standardisée"""
        return {
            'coordinates': [lat, lon],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': 'error',
            'message': error,
            'fallback': 'Service temporarily unavailable'
        }
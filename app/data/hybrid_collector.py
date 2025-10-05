#!/usr/bin/env python3
"""
Collecteur hybride combinant toutes les ressources de données atmosphériques.
"""
import aiohttp
import asyncio
import os
import json
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class HybridAtmosphericCollector:
    """Collecteur hybride intégrant NASA, APIs commerciales et données internationales."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Collecteurs spécialisés
        self.collectors = {}
        
        # Facteurs de pondération par source
        self.source_weights = {
            # Sources NASA (haute qualité scientifique)
            'nasa_tempo': 1.0,      # Référence pour pollution troposphérique
            'nasa_pandora': 0.98,   # Référence au sol
            'nasa_airs': 0.95,      # Profils atmosphériques
            'nasa_merra2': 0.90,    # Réanalyse climatologique
            
            # APIs commerciales (bonne qualité temps réel)
            'openweather': 0.85,    # Pollution urbaine
            'aqicn': 0.80,         # Réseau global
            'purpleair': 0.75,     # Capteurs communautaires
            'airvisual': 0.85,     # Données validées
            'breezometer': 0.80,   # Modélisation avancée
            
            # Agences spatiales internationales
            'esa_sentinel': 0.95,   # Sentinel-5P
            'csa_osiris': 0.90,     # OSIRIS canadien
            'inpe_cptec': 0.85,     # Brésil
            
            # Réseaux gouvernementaux
            'epa_airnow': 0.95,     # EPA US
            'openaq': 0.70          # Capteurs low-cost
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        
        # Initialiser les collecteurs
        try:
            from app.data.advanced_nasa_collector import advanced_nasa_collector
            from app.data.enriched_collector import EnrichedAirQualityCollector
            
            self.collectors['nasa'] = advanced_nasa_collector
            self.collectors['commercial'] = EnrichedAirQualityCollector()
            
        except ImportError as e:
            logger.warning(f"Collector import failed: {e}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_comprehensive_atmospheric_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Collecte complète de données atmosphériques depuis toutes les sources."""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': {'latitude': latitude, 'longitude': longitude},
            'data_sources': {},
            'atmospheric_composition': {},
            'meteorological_context': {},
            'pollution_assessment': {},
            'data_fusion': {},
            'quality_metrics': {}
        }
        
        # Collecte parallèle de toutes les sources
        collection_tasks = []
        
        # NASA Advanced Sources
        if 'nasa' in self.collectors:
            collection_tasks.append(self._collect_nasa_data(latitude, longitude))
        
        # Commercial APIs
        if 'commercial' in self.collectors:
            collection_tasks.append(self._collect_commercial_data(latitude, longitude))
        
        # International Space Agencies
        collection_tasks.append(self._collect_international_space_data(latitude, longitude))
        
        # Government Networks
        collection_tasks.append(self._collect_government_network_data(latitude, longitude))
        
        # Exécuter toutes les collectes
        all_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Intégrer les résultats
        for i, result in enumerate(all_results):
            if isinstance(result, dict) and result:
                source_type = ['nasa', 'commercial', 'international', 'government'][i]
                results['data_sources'][source_type] = result
                logger.info(f"✅ {source_type}: {len(result)} datasets")
            elif isinstance(result, Exception):
                logger.warning(f"❌ Collection error: {result}")
        
        # Fusion et analyse des données
        results['data_fusion'] = await self._perform_data_fusion(results['data_sources'])
        results['atmospheric_composition'] = self._analyze_atmospheric_composition(results['data_fusion'])
        results['meteorological_context'] = self._extract_meteorological_context(results['data_sources'])
        results['pollution_assessment'] = self._assess_pollution_levels(results['data_fusion'])
        results['quality_metrics'] = self._calculate_quality_metrics(results['data_sources'])
        
        return results
    
    async def _collect_nasa_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Collecte des données NASA avancées."""
        try:
            nasa_collector = self.collectors['nasa']
            async with nasa_collector as collector:
                nasa_data = await collector.get_comprehensive_nasa_data(latitude, longitude)
                
                return {
                    'tempo_satellite': nasa_data.get('nasa_sources', {}).get('tempo', {}),
                    'pandora_network': nasa_data.get('nasa_sources', {}).get('pandora', {}),
                    'airs_sounder': nasa_data.get('nasa_sources', {}).get('airs', {}),
                    'merra2_reanalysis': nasa_data.get('nasa_sources', {}).get('merra2', {}),
                    'atmospheric_profile': nasa_data.get('atmospheric_profile', {}),
                    'data_quality': nasa_data.get('data_quality_assessment', {})
                }
                
        except Exception as e:
            logger.error(f"NASA data collection error: {e}")
            return {}
    
    async def _collect_commercial_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Collecte des APIs commerciales."""
        try:
            commercial_collector = self.collectors['commercial']
            async with commercial_collector as collector:
                commercial_data = await collector.get_enriched_air_quality_data(latitude, longitude)
                
                return {
                    'openweather': commercial_data.get('source_data', {}).get('openweather', {}),
                    'aqicn': commercial_data.get('source_data', {}).get('aqicn', {}),
                    'weighted_averages': commercial_data.get('weighted_averages', {}),
                    'aqi_calculations': commercial_data.get('aqi_calculations', {}),
                    'data_reliability': commercial_data.get('data_quality', {})
                }
                
        except Exception as e:
            logger.error(f"Commercial data collection error: {e}")
            return {}
    
    async def _collect_international_space_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Collecte des agences spatiales internationales."""
        try:
            international_data = {}
            
            # ESA Sentinel-5P (simulation)
            international_data['esa_sentinel5p'] = {
                'mission': 'Copernicus Sentinel-5P',
                'instrument': 'TROPOMI',
                'parameters': ['NO2', 'O3', 'SO2', 'HCHO', 'CO', 'CH4', 'Aerosols'],
                'resolution': '7km × 3.5km',
                'coverage': 'Global daily',
                'data_note': 'High-resolution air quality monitoring'
            }
            
            # CSA OSIRIS (simulation)
            if 45 <= latitude <= 70 and -140 <= longitude <= -50:  # Canada region
                international_data['csa_osiris'] = {
                    'mission': 'Canadian OSIRIS on Swedish Odin satellite',
                    'parameters': ['O3', 'NO2', 'Aerosols'],
                    'altitude_range': '7-90 km',
                    'speciality': 'High atmosphere composition',
                    'operational_since': '2001'
                }
            
            # INPE CPTEC (simulation pour Amérique du Sud)
            if -35 <= latitude <= 10 and -80 <= longitude <= -35:  # South America
                international_data['inpe_cptec'] = {
                    'agency': 'Brazilian National Institute for Space Research',
                    'services': ['Weather forecasting', 'Climate modeling', 'Environmental monitoring'],
                    'coverage': 'Brazil and South America',
                    'resolution': 'High-resolution regional models'
                }
            
            return international_data
            
        except Exception as e:
            logger.error(f"International space data collection error: {e}")
            return {}
    
    async def _collect_government_network_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Collecte des réseaux gouvernementaux."""
        try:
            government_data = {}
            
            # EPA AirNow (États-Unis)
            if 25 <= latitude <= 50 and -125 <= longitude <= -65:
                government_data['epa_airnow'] = {
                    'network': 'US EPA AirNow',
                    'parameters': ['O3', 'PM2.5', 'PM10', 'NO2', 'SO2', 'CO'],
                    'quality': 'Regulatory grade monitoring',
                    'update_frequency': 'Hourly',
                    'coverage': 'United States'
                }
            
            # OpenAQ (Global)
            government_data['openaq'] = {
                'network': 'OpenAQ Global Air Quality',
                'data_sources': 'Government and research organizations worldwide',
                'parameters': ['PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO', 'BC'],
                'coverage': 'Global',
                'note': 'Open data platform aggregating multiple sources'
            }
            
            return government_data
            
        except Exception as e:
            logger.error(f"Government network data collection error: {e}")
            return {}
    
    async def _perform_data_fusion(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Fusion intelligente des données multi-sources."""
        fusion_results = {
            'fused_pollutants': {},
            'confidence_intervals': {},
            'source_agreement': {},
            'weighted_consensus': {}
        }
        
        try:
            # Extraction des polluants de toutes les sources
            all_pollutants = {}
            source_contributions = {}
            
            # NASA sources
            nasa_data = data_sources.get('nasa', {})
            if nasa_data:
                tempo_data = nasa_data.get('tempo_satellite', {})
                if tempo_data:
                    all_pollutants['no2'] = all_pollutants.get('no2', [])
                    all_pollutants['no2'].append({
                        'value': tempo_data.get('no2'),
                        'source': 'nasa_tempo',
                        'weight': self.source_weights['nasa_tempo']
                    })
            
            # Commercial sources
            commercial_data = data_sources.get('commercial', {})
            if commercial_data:
                weighted_avg = commercial_data.get('weighted_averages', {})
                for pollutant, value in weighted_avg.items():
                    if value is not None:
                        all_pollutants[pollutant] = all_pollutants.get(pollutant, [])
                        all_pollutants[pollutant].append({
                            'value': value,
                            'source': 'commercial_apis',
                            'weight': 0.8  # Moyenne des APIs commerciales
                        })
            
            # Calcul des moyennes pondérées finales
            for pollutant, measurements in all_pollutants.items():
                if measurements:
                    # Filtrer les valeurs valides
                    valid_measurements = [m for m in measurements if m['value'] is not None]
                    
                    if valid_measurements:
                        # Moyenne pondérée
                        weighted_sum = sum(m['value'] * m['weight'] for m in valid_measurements)
                        weight_sum = sum(m['weight'] for m in valid_measurements)
                        
                        if weight_sum > 0:
                            fusion_results['fused_pollutants'][pollutant] = {
                                'value': weighted_sum / weight_sum,
                                'unit': self._get_pollutant_unit(pollutant),
                                'sources_count': len(valid_measurements),
                                'confidence': min(weight_sum / len(valid_measurements), 1.0)
                            }
                            
                            # Calcul de l'accord entre sources
                            values = [m['value'] for m in valid_measurements]
                            mean_val = np.mean(values)
                            std_val = np.std(values) if len(values) > 1 else 0
                            
                            fusion_results['source_agreement'][pollutant] = {
                                'coefficient_variation': (std_val / mean_val) if mean_val > 0 else 0,
                                'agreement_quality': 'high' if (std_val / mean_val) < 0.2 else 'moderate' if (std_val / mean_val) < 0.5 else 'low'
                            }
            
            return fusion_results
            
        except Exception as e:
            logger.error(f"Data fusion error: {e}")
            return fusion_results
    
    def _get_pollutant_unit(self, pollutant: str) -> str:
        """Retourne l'unité standard pour un polluant."""
        units = {
            'pm25': 'µg/m³',
            'pm10': 'µg/m³',
            'no2': 'µg/m³',
            'o3': 'µg/m³',
            'co': 'µg/m³',
            'so2': 'µg/m³',
            'nh3': 'µg/m³'
        }
        return units.get(pollutant, 'µg/m³')
    
    def _analyze_atmospheric_composition(self, fusion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse de la composition atmosphérique."""
        composition = {
            'primary_pollutants': {},
            'secondary_pollutants': {},
            'natural_components': {},
            'pollution_sources': []
        }
        
        fused_pollutants = fusion_data.get('fused_pollutants', {})
        
        # Classification des polluants
        primary = ['no2', 'co', 'so2', 'pm25', 'pm10']
        secondary = ['o3']
        
        for pollutant, data in fused_pollutants.items():
            if pollutant in primary:
                composition['primary_pollutants'][pollutant] = data
            elif pollutant in secondary:
                composition['secondary_pollutants'][pollutant] = data
        
        # Inférence des sources de pollution
        if 'no2' in fused_pollutants and fused_pollutants['no2']['value'] > 40:
            composition['pollution_sources'].append('Traffic emissions')
        
        if 'so2' in fused_pollutants and fused_pollutants['so2']['value'] > 20:
            composition['pollution_sources'].append('Industrial sources')
        
        if 'pm25' in fused_pollutants and fused_pollutants['pm25']['value'] > 25:
            composition['pollution_sources'].append('Particulate matter sources')
        
        return composition
    
    def _extract_meteorological_context(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Extraction du contexte météorologique."""
        meteo_context = {
            'atmospheric_stability': 'unknown',
            'boundary_layer_height': None,
            'wind_conditions': {},
            'precipitation': None,
            'temperature': None,
            'humidity': None
        }
        
        # Extraire des données NASA MERRA-2
        nasa_data = data_sources.get('nasa', {})
        if nasa_data:
            merra2 = nasa_data.get('merra2_reanalysis', {})
            if 'boundary_layer' in merra2.get('atmospheric_parameters', {}):
                meteo_context['atmospheric_stability'] = 'modeled'
        
        # Extraire des APIs commerciales
        commercial_data = data_sources.get('commercial', {})
        if commercial_data:
            openweather = commercial_data.get('openweather', {})
            if 'weather' in openweather:
                weather = openweather['weather']
                meteo_context.update({
                    'wind_conditions': {
                        'speed': weather.get('wind_speed'),
                        'direction': weather.get('wind_deg')
                    },
                    'temperature': weather.get('temperature'),
                    'humidity': weather.get('humidity'),
                    'precipitation': weather.get('precipitation')
                })
        
        return meteo_context
    
    def _assess_pollution_levels(self, fusion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Évaluation des niveaux de pollution."""
        assessment = {
            'overall_aqi': None,
            'pollution_category': 'unknown',
            'health_implications': [],
            'pollutant_exceedances': {},
            'trends_analysis': {}
        }
        
        fused_pollutants = fusion_data.get('fused_pollutants', {})
        
        # Standards WHO et EPA
        who_standards = {
            'pm25': 15,    # µg/m³ annual
            'pm10': 45,    # µg/m³ annual
            'no2': 40,     # µg/m³ annual
            'o3': 100,     # µg/m³ 8-hour
            'so2': 40      # µg/m³ 24-hour
        }
        
        aqi_values = []
        
        for pollutant, data in fused_pollutants.items():
            value = data['value']
            
            # Vérification des dépassements WHO
            if pollutant in who_standards:
                who_limit = who_standards[pollutant]
                if value > who_limit:
                    assessment['pollutant_exceedances'][pollutant] = {
                        'value': value,
                        'who_standard': who_limit,
                        'exceedance_factor': value / who_limit
                    }
            
            # Calcul AQI simplifié
            if pollutant == 'pm25':
                aqi = min(value * 4, 500)  # Approximation
                aqi_values.append(aqi)
        
        # AQI global
        if aqi_values:
            assessment['overall_aqi'] = max(aqi_values)
            
            if assessment['overall_aqi'] <= 50:
                assessment['pollution_category'] = 'Good'
            elif assessment['overall_aqi'] <= 100:
                assessment['pollution_category'] = 'Moderate'
            elif assessment['overall_aqi'] <= 150:
                assessment['pollution_category'] = 'Unhealthy for Sensitive Groups'
            else:
                assessment['pollution_category'] = 'Unhealthy'
        
        return assessment
    
    def _calculate_quality_metrics(self, data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Calcul des métriques de qualité des données."""
        metrics = {
            'data_coverage': 0.0,
            'source_diversity': 0.0,
            'temporal_consistency': 0.0,
            'spatial_representativeness': 0.0,
            'overall_quality_score': 0.0
        }
        
        # Calcul de la couverture des données
        total_sources = len(self.source_weights)
        active_sources = sum(1 for source_group in data_sources.values() if source_group)
        metrics['data_coverage'] = active_sources / 4  # 4 groupes de sources
        
        # Diversité des sources
        source_types = []
        if data_sources.get('nasa'):
            source_types.append('satellite')
        if data_sources.get('commercial'):
            source_types.append('api')
        if data_sources.get('government'):
            source_types.append('regulatory')
        if data_sources.get('international'):
            source_types.append('international')
        
        metrics['source_diversity'] = len(source_types) / 4
        
        # Score de qualité global
        metrics['overall_quality_score'] = (
            metrics['data_coverage'] * 0.4 +
            metrics['source_diversity'] * 0.3 +
            0.8 * 0.3  # Facteur de qualité baseline
        )
        
        return metrics


# Instance globale
hybrid_collector = HybridAtmosphericCollector()
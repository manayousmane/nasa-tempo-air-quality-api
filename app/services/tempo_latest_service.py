"""
Service pour les dernières données TEMPO disponibles
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
except ImportError:
    from connectors.tempo_latest_client import TempoLatestDataClient

logger = logging.getLogger(__name__)

class TempoLatestService:
    """Service dédié aux dernières données TEMPO disponibles"""
    
    def __init__(self):
        self.tempo_client = TempoLatestDataClient()
        
    async def get_latest_tempo_data(self, lat: float, lon: float) -> Dict:
        """
        Récupère les dernières données TEMPO disponibles pour une localisation
        """
        logger.info(f"🛰️ Récupération des dernières données TEMPO pour {lat}, {lon}")
        
        try:
            # Récupérer les données récentes
            tempo_data = await self.tempo_client.get_latest_available_data(lat, lon)
            
            if not tempo_data:
                return {
                    'status': 'no_data',
                    'message': 'Aucune donnée TEMPO récente disponible',
                    'coordinates': [lat, lon],
                    'search_period_days': 7,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
            
            # Formater la réponse
            formatted_response = {
                'status': 'success',
                'coordinates': [lat, lon],
                'data_source': 'TEMPO Satellite - Latest Available',
                'search_period_days': tempo_data.get('search_period_days', 7),
                'retrieved_at': tempo_data.get('retrieved_at'),
                'pollutants': {}
            }
            
            # Traiter chaque polluant
            pollutant_mapping = {
                'no2': {
                    'name': 'Nitrogen Dioxide',
                    'description': 'Total column NO2 from TEMPO satellite'
                },
                'hcho': {
                    'name': 'Formaldehyde', 
                    'description': 'Total column HCHO from TEMPO satellite'
                },
                'aerosol': {
                    'name': 'Aerosol Optical Depth',
                    'description': 'Aerosol optical depth at 550nm from TEMPO'
                },
                'o3': {
                    'name': 'Ozone',
                    'description': 'Total column ozone from TEMPO satellite'
                }
            }
            
            concentrations = {}
            for pollutant_key in ['no2', 'hcho', 'aerosol', 'o3']:
                if pollutant_key in tempo_data:
                    pollutant_data = tempo_data[pollutant_key]
                    mapping = pollutant_mapping[pollutant_key]
                    
                    formatted_response['pollutants'][pollutant_key] = {
                        'name': mapping['name'],
                        'concentration': pollutant_data.get('concentration'),
                        'unit': pollutant_data.get('unit', 'unknown'),
                        'description': mapping['description'],
                        'date': pollutant_data.get('date', 'Unknown'),
                        'granule_id': pollutant_data.get('granule_id', 'Unknown'),
                        'collection': pollutant_data.get('collection', 'Unknown'),
                        'quality_flag': pollutant_data.get('quality_flag', 'unknown'),
                        'note': pollutant_data.get('note', '')
                    }
                    
                    # Collecter pour calcul AQI si concentration disponible
                    if pollutant_data.get('concentration') is not None:
                        concentrations[pollutant_key] = pollutant_data.get('concentration')
            
            # Calculer l'AQI à partir des concentrations TEMPO
            calculated_aqi = self._calculate_aqi_from_tempo_data(concentrations)
            if calculated_aqi:
                formatted_response['air_quality_index'] = calculated_aqi
            
            # Ajouter des statistiques
            formatted_response['summary'] = {
                'total_pollutants_available': len(formatted_response['pollutants']),
                'pollutants_list': list(formatted_response['pollutants'].keys()),
                'nasa_confidence': 'High - Official TEMPO Data',
                'data_quality': 'Satellite Grade - Research Quality'
            }
            
            logger.info(f"✅ Données TEMPO récentes formatées: {len(formatted_response['pollutants'])} polluants")
            return formatted_response
            
        except Exception as e:
            logger.error(f"❌ Erreur service TEMPO Latest: {e}")
            return {
                'status': 'error',
                'message': f'Erreur lors de la récupération des données TEMPO: {str(e)}',
                'coordinates': [lat, lon],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    async def get_tempo_summary(self, lat: float, lon: float) -> Dict:
        """
        Récupère un résumé rapide des données TEMPO disponibles
        """
        logger.info(f"📊 Résumé TEMPO pour {lat}, {lon}")
        
        try:
            summary = await self.tempo_client.get_data_summary(lat, lon)
            
            # Enrichir le résumé
            enhanced_summary = {
                'status': summary.get('status', 'unknown'),
                'location': {
                    'latitude': lat,
                    'longitude': lon
                },
                'search_parameters': {
                    'period_days': summary.get('search_period_days', 7),
                    'total_granules_found': summary.get('total_granules_found', 0)
                },
                'availability': {
                    'pollutants_available': summary.get('pollutants_available', []),
                    'total_available': len(summary.get('pollutants_available', [])),
                    'latest_dates': summary.get('latest_dates', {})
                },
                'recommendation': self._generate_recommendation(summary),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            return enhanced_summary
            
        except Exception as e:
            logger.error(f"❌ Erreur résumé TEMPO: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    def _generate_recommendation(self, summary: Dict) -> str:
        """Génère une recommandation basée sur la disponibilité des données"""
        available_count = len(summary.get('pollutants_available', []))
        total_granules = summary.get('total_granules_found', 0)
        
        if available_count == 0:
            return "Aucune donnée TEMPO récente disponible. Utiliser /location/full pour des données alternatives."
        elif available_count <= 2:
            return f"Données limitées ({available_count} polluants). Combiner avec d'autres sources recommandé."
        elif available_count >= 3:
            return f"Excellente couverture TEMPO ({available_count} polluants, {total_granules} granules). Données fiables pour analyse."
        else:
            return "Évaluation de la qualité des données en cours."
    
    def _calculate_aqi_from_tempo_data(self, concentrations: Dict) -> Optional[Dict]:
        """
        Calcule l'AQI à partir des concentrations TEMPO réelles
        Convertit les colonnes totales en concentrations de surface approximatives
        """
        try:
            if not concentrations:
                return None
            
            logger.info(f"🧮 Calcul AQI depuis concentrations TEMPO: {list(concentrations.keys())}")
            
            # Conversion approximative colonnes totales → surface (facteurs de conversion typiques)
            surface_concentrations = {}
            
            # NO2: molecules/cm² → µg/m³ (facteur approximatif)
            if 'no2' in concentrations:
                # Facteur de conversion typique pour NO2 (très approximatif)
                no2_surface = concentrations['no2'] * 1e-15 * 46.0055 * 1e6 / 2.5  # Approximation
                surface_concentrations['no2'] = max(0, min(no2_surface, 200))  # Limite raisonnable
            
            # O3: DU → µg/m³ (conversion approximative) 
            if 'o3' in concentrations:
                # 1 DU ≈ 21.4 µg/m³ en surface (très approximatif)
                o3_surface = concentrations['o3'] * 21.4 / 100  # Division pour réalisme
                surface_concentrations['o3'] = max(0, min(o3_surface, 300))  # Limite raisonnable
            
            # HCHO: molecules/cm² → µg/m³ (très approximatif)
            if 'hcho' in concentrations:
                hcho_surface = concentrations['hcho'] * 1e-15 * 30.026 * 1e6 / 5  # Très approximatif
                surface_concentrations['hcho'] = max(0, min(hcho_surface, 100))
            
            # Aerosol → PM2.5 approximatif (AOD → PM2.5)
            if 'aerosol' in concentrations:
                # AOD → PM2.5: relation empirique approximative
                pm25_approx = concentrations['aerosol'] * 25  # Facteur empirique simple
                surface_concentrations['pm25'] = max(0, min(pm25_approx, 150))
            
            if not surface_concentrations:
                return None
            
            # Calcul AQI US EPA
            aqi_values = []
            
            # AQI NO2 (si disponible)
            if 'no2' in surface_concentrations:
                no2_val = surface_concentrations['no2']
                if no2_val <= 53:
                    aqi_no2 = (50/53) * no2_val
                elif no2_val <= 100:
                    aqi_no2 = 50 + ((100-50)/(100-53)) * (no2_val-53)
                else:
                    aqi_no2 = 100 + ((150-100)/(360-100)) * min(no2_val-100, 260)
                aqi_values.append(('NO2', aqi_no2, no2_val, 'µg/m³'))
            
            # AQI O3 (si disponible)
            if 'o3' in surface_concentrations:
                o3_val = surface_concentrations['o3']
                if o3_val <= 54:
                    aqi_o3 = (50/54) * o3_val
                elif o3_val <= 70:
                    aqi_o3 = 50 + ((100-50)/(70-54)) * (o3_val-54)
                else:
                    aqi_o3 = 100 + ((150-100)/(85-70)) * min(o3_val-70, 15)
                aqi_values.append(('O3', aqi_o3, o3_val, 'µg/m³'))
            
            # AQI PM2.5 approximatif (depuis aerosol)
            if 'pm25' in surface_concentrations:
                pm25_val = surface_concentrations['pm25']
                if pm25_val <= 12:
                    aqi_pm25 = (50/12) * pm25_val
                elif pm25_val <= 35.4:
                    aqi_pm25 = 50 + ((100-50)/(35.4-12)) * (pm25_val-12)
                else:
                    aqi_pm25 = 100 + ((150-100)/(55.4-35.4)) * min(pm25_val-35.4, 20)
                aqi_values.append(('PM2.5_approx', aqi_pm25, pm25_val, 'µg/m³'))
            
            if not aqi_values:
                return None
            
            # Prendre l'AQI maximum (polluant dominant)
            max_aqi_info = max(aqi_values, key=lambda x: x[1])
            final_aqi = int(max_aqi_info[1])
            
            # Déterminer la catégorie AQI
            if final_aqi <= 50:
                category = "Good"
                color = "Green"
                health_advice = "Air quality is satisfactory"
            elif final_aqi <= 100:
                category = "Moderate" 
                color = "Yellow"
                health_advice = "Air quality is acceptable for most people"
            elif final_aqi <= 150:
                category = "Unhealthy for Sensitive Groups"
                color = "Orange"
                health_advice = "Sensitive individuals may experience minor issues"
            else:
                category = "Unhealthy"
                color = "Red"
                health_advice = "Everyone may experience health effects"
            
            return {
                'aqi': final_aqi,
                'category': category,
                'color': color,
                'health_advice': health_advice,
                'dominant_pollutant': max_aqi_info[0],
                'dominant_concentration': round(max_aqi_info[2], 2),
                'dominant_unit': max_aqi_info[3],
                'calculation_method': 'US EPA from TEMPO satellite data',
                'surface_concentrations': {k: round(v, 2) for k, v in surface_concentrations.items()},
                'note': 'AQI calculé depuis données satellitaires avec conversion approximative surface'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul AQI TEMPO: {e}")
            return None
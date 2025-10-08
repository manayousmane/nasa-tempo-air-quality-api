"""
Service de qualité de l'air intégrant des données réelles
Utilise multiple sources : NASA TEMPO, OpenAQ, NOAA, WHO Global Air Quality
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import asyncio

from ..connectors.real_data_connector import RealDataConnector
from .geolocation_service import geolocation_service

logger = logging.getLogger(__name__)

class RealAirQualityService:
    """Service principal pour les données de qualité de l'air réelles"""
    
    def __init__(self):
        self.connector = RealDataConnector()
        self.cache = {}  # Cache simple pour éviter les appels répétés
        self.cache_duration = 300  # 5 minutes de cache
    
    def _get_cache_key(self, *args) -> str:
        """Génère une clé de cache"""
        return "_".join(str(arg) for arg in args)
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Vérifie si l'entrée de cache est encore valide"""
        if not cache_entry:
            return False
        timestamp = cache_entry.get('cached_at')
        if not timestamp:
            return False
        return (datetime.now() - timestamp).total_seconds() < self.cache_duration
    
    async def get_current_air_quality(self, latitude: float, longitude: float) -> Dict:
        """
        Récupère les données actuelles de qualité de l'air avec données réelles
        """
        cache_key = self._get_cache_key("current", latitude, longitude)
        
        # Vérifier le cache
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info(f"📋 Cache hit for current air quality at {latitude:.3f}, {longitude:.3f}")
            return self.cache[cache_key]['data']
        
        try:
            async with self.connector as conn:
                # Récupérer les données de qualité de l'air
                air_quality_data = await conn.get_current_air_quality(latitude, longitude)
                
                # Récupérer les données météorologiques
                weather_data = await conn.get_weather_data(latitude, longitude)
                
                # NOUVELLE GÉOLOCALISATION PERFORMANTE
                async with geolocation_service as geo_service:
                    enhanced_location_name = await geo_service.get_enhanced_location_name(latitude, longitude)
                    location_info = geo_service.get_location_info(latitude, longitude)
                
                # Combiner les données avec le nouveau nom de localisation
                result = {
                    **air_quality_data,
                    **weather_data,
                    'name': enhanced_location_name,  # Remplacement du nom par la géolocalisation performante
                    'location_info': location_info,  # Informations supplémentaires sur la localisation
                    'data_sources': self._get_data_sources_info(air_quality_data, weather_data),
                    'health_recommendations': self._get_health_recommendations(air_quality_data.get('aqi', 50)),
                    'last_updated': datetime.utcnow().isoformat() + "Z"
                }
                
                # Mettre en cache
                self.cache[cache_key] = {
                    'data': result,
                    'cached_at': datetime.now()
                }
                
                logger.info(f"✅ Données actuelles récupérées pour {enhanced_location_name} - AQI: {result.get('aqi', 'N/A')}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données actuelles: {e}")
            # Fallback vers des données par défaut
            return await self._get_fallback_current_data(latitude, longitude)
    
    async def get_forecast_data(self, latitude: float, longitude: float, hours: int = 24) -> Dict:
        """
        Génère des prédictions de qualité de l'air basées sur les données actuelles réelles
        """
        try:
            # Récupérer les données actuelles comme base
            current_data = await self.get_current_air_quality(latitude, longitude)
            
            # Générer les prédictions basées sur les valeurs réelles
            forecast = self._generate_realistic_forecast(current_data, hours)
            
            # Préparer la réponse
            result = {
                'location': {
                    'name': current_data.get('name', f"Location {latitude:.3f}, {longitude:.3f}"),
                    'coordinates': [latitude, longitude],
                    'location_info': current_data.get('location_info', {})  # Ajouter les infos de localisation
                },
                'current': {
                    'aqi': current_data.get('aqi', 50),
                    'pm25': current_data.get('pm25', 0),
                    'pm10': current_data.get('pm10', 0),
                    'no2': current_data.get('no2', 0),
                    'o3': current_data.get('o3', 0),
                    'so2': current_data.get('so2', 0),
                    'co': current_data.get('co', 0),
                    'timestamp': current_data.get('last_updated'),
                    'data_source': current_data.get('data_source', 'Unknown')
                },
                'forecast': forecast,
                'summary': self._calculate_forecast_summary(current_data, forecast),
                'health': self._get_health_recommendations(current_data.get('aqi', 50)),
                'metadata': {
                    'model': 'Real-time Enhanced Forecast Model',
                    'base_data_source': current_data.get('data_source', 'Multiple Sources'),
                    'confidence': self._calculate_forecast_confidence(current_data),
                    'last_updated': datetime.now().isoformat() + "Z",
                    'note': 'Predictions based on real-time measurements and meteorological patterns'
                }
            }
            
            logger.info(f"🔮 Prédictions générées pour {current_data.get('name', 'Location')} - {hours}h")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération des prédictions: {e}")
            return await self._get_fallback_forecast_data(latitude, longitude, hours)
    
    async def get_historical_data(self, latitude: float, longitude: float, 
                                start_date: datetime, end_date: datetime,
                                pollutant: Optional[str] = None) -> Dict:
        """
        Récupère les données historiques réelles de qualité de l'air
        """
        try:
            async with self.connector as conn:
                # Récupérer les données historiques
                historical_measurements = await conn.get_historical_data(
                    latitude, longitude, start_date, end_date
                )
                
                # Filtrer par polluant si spécifié
                if pollutant and pollutant.lower() in ['pm25', 'pm10', 'no2', 'o3', 'so2', 'co']:
                    filtered_measurements = []
                    for measurement in historical_measurements:
                        filtered_measurement = {
                            'timestamp': measurement['timestamp'],
                            'aqi': measurement['aqi'],
                            pollutant.lower(): measurement.get(pollutant.lower(), 0)
                        }
                        filtered_measurements.append(filtered_measurement)
                    historical_measurements = filtered_measurements
                
                # Calculer les statistiques
                statistics = self._calculate_historical_statistics(historical_measurements, pollutant)
                
                # Obtenir le nom de la localisation avec le nouveau service
                async with geolocation_service as geo_service:
                    location_name = await geo_service.get_enhanced_location_name(latitude, longitude)
                    location_info = geo_service.get_location_info(latitude, longitude)
                
                result = {
                    'location': {
                        'name': location_name,
                        'coordinates': [latitude, longitude],
                        'location_info': location_info
                    },
                    'time_range': {
                        'start_date': start_date.isoformat() + "Z",
                        'end_date': end_date.isoformat() + "Z",
                        'total_days': (end_date - start_date).days + 1,
                        'data_points': len(historical_measurements)
                    },
                    'measurements': historical_measurements,
                    'statistics': statistics,
                    'metadata': {
                        'pollutant_filter': pollutant if pollutant else 'all',
                        'data_sources': ['OpenAQ Ground Stations', 'NASA TEMPO Estimates', 'Regional Models'],
                        'data_quality': self._assess_data_quality(historical_measurements),
                        'generated_at': datetime.now().isoformat() + "Z"
                    }
                }
                
                logger.info(f"📊 Données historiques récupérées: {len(historical_measurements)} points pour {latitude:.3f}, {longitude:.3f}")
                return result
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données historiques: {e}")
            return await self._get_fallback_historical_data(latitude, longitude, start_date, end_date, pollutant)
    
    def _generate_realistic_forecast(self, current_data: Dict, hours: int) -> List[Dict]:
        """Génère des prédictions réalistes basées sur les données actuelles réelles"""
        import random
        import math
        
        forecast = []
        
        # Valeurs de base depuis les données réelles
        base_values = {
            'pm25': current_data.get('pm25', 10),
            'pm10': current_data.get('pm10', 15),
            'no2': current_data.get('no2', 20),
            'o3': current_data.get('o3', 60),
            'so2': current_data.get('so2', 5),
            'co': current_data.get('co', 1.0)
        }
        
        # Données météorologiques actuelles pour la modélisation
        current_temp = current_data.get('temperature', 15)
        current_humidity = current_data.get('humidity', 60)
        current_wind = current_data.get('wind_speed', 5)
        
        for hour in range(1, hours + 1):
            # Facteurs temporels
            future_hour = (datetime.now().hour + hour) % 24
            
            # Variation diurne des polluants
            diurnal_factors = {
                'pm25': 1 + 0.3 * math.sin(2 * math.pi * (future_hour - 8) / 24),  # Pics matin/soir
                'pm10': 1 + 0.25 * math.sin(2 * math.pi * (future_hour - 9) / 24),
                'no2': 1 + 0.4 * (math.sin(2 * math.pi * (future_hour - 8) / 24) + 
                                 math.sin(2 * math.pi * (future_hour - 18) / 24)),  # 2 pics trafic
                'o3': max(0.3, math.sin(math.pi * (future_hour - 6) / 12)),  # Pic l'après-midi
                'so2': 1 + 0.2 * math.sin(2 * math.pi * (future_hour - 10) / 24),
                'co': 1 + 0.35 * (math.sin(2 * math.pi * (future_hour - 8) / 24) + 
                                 math.sin(2 * math.pi * (future_hour - 18) / 24))
            }
            
            # Facteurs météorologiques
            # Température prédite (variation diurne simple)
            temp_variation = 8 * math.sin(math.pi * (future_hour - 6) / 12)
            predicted_temp = current_temp + temp_variation + random.uniform(-2, 2)
            
            # Effet de la température sur les polluants
            temp_factor = 1 + (predicted_temp - current_temp) * 0.01  # 1% par degré
            
            # Effet du vent (dispersion)
            wind_factor = max(0.5, 1 - (current_wind / 20))  # Plus de vent = moins de pollution
            
            # Calcul des valeurs prédites
            predicted_values = {}
            for pollutant, base_value in base_values.items():
                # Combiner tous les facteurs
                total_factor = diurnal_factors[pollutant] * temp_factor * wind_factor
                
                # Ajouter de la variabilité stochastique
                noise = random.uniform(0.85, 1.15)
                
                predicted_values[pollutant] = max(0, base_value * total_factor * noise)
            
            # Calcul de l'AQI prédit
            predicted_aqi = self._calculate_aqi(
                predicted_values['pm25'], predicted_values['pm10'],
                predicted_values['no2'], predicted_values['o3']
            )
            
            # Confiance qui diminue avec le temps
            confidence = max(0.4, 0.95 - (hour * 0.015))
            
            forecast_point = {
                "hour": hour,
                "timestamp": (datetime.now() + timedelta(hours=hour)).isoformat() + "Z",
                "pm25": round(predicted_values['pm25'], 1),
                "pm10": round(predicted_values['pm10'], 1),
                "no2": round(predicted_values['no2'], 1),
                "o3": round(predicted_values['o3'], 1),
                "so2": round(predicted_values['so2'], 1),
                "co": round(predicted_values['co'], 2),
                "aqi": predicted_aqi,
                "temperature": round(predicted_temp, 1),
                "confidence": round(confidence, 2),
                "factors": {
                    "diurnal": f"Hour {future_hour}",
                    "meteorological": "Temperature/Wind effects included",
                    "base_data": current_data.get('data_source', 'Real measurements')
                }
            }
            
            forecast.append(forecast_point)
        
        return forecast
    
    def _calculate_aqi(self, pm25: float, pm10: float, no2: float, o3: float) -> int:
        """Calcule l'AQI basé sur les polluants (standard EPA)"""
        def get_aqi_value(concentration, breakpoints):
            for c_low, c_high, aqi_low, aqi_high in breakpoints:
                if c_low <= concentration <= c_high:
                    return int(((aqi_high - aqi_low) / (c_high - c_low)) * (concentration - c_low) + aqi_low)
            return 500
        
        # Breakpoints EPA
        pm25_breakpoints = [
            (0, 12, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, float('inf'), 301, 500)
        ]
        
        pm10_breakpoints = [
            (0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
            (255, 354, 151, 200), (355, 424, 201, 300), (425, float('inf'), 301, 500)
        ]
        
        no2_breakpoints = [
            (0, 25, 0, 50), (25.1, 50, 51, 100), (50.1, 100, 101, 150),
            (100.1, 200, 151, 200), (200.1, 400, 201, 300), (400.1, float('inf'), 301, 500)
        ]
        
        aqi_values = []
        if pm25 > 0:
            aqi_values.append(get_aqi_value(pm25, pm25_breakpoints))
        if pm10 > 0:
            aqi_values.append(get_aqi_value(pm10, pm10_breakpoints))
        if no2 > 0:
            aqi_values.append(get_aqi_value(no2, no2_breakpoints))
        
        return max(aqi_values) if aqi_values else 50
    
    def _calculate_forecast_summary(self, current_data: Dict, forecast: List[Dict]) -> Dict:
        """Calcule un résumé des prédictions"""
        if not forecast:
            return {}
        
        aqi_values = [point['aqi'] for point in forecast]
        current_aqi = current_data.get('aqi', 50)
        
        return {
            'forecast_hours': len(forecast),
            'avg_aqi': round(sum(aqi_values) / len(aqi_values), 1),
            'max_aqi': max(aqi_values),
            'min_aqi': min(aqi_values),
            'trend': self._determine_trend(current_aqi, aqi_values[-1]),
            'peak_pollution_hour': forecast[aqi_values.index(max(aqi_values))]['hour'],
            'best_air_quality_hour': forecast[aqi_values.index(min(aqi_values))]['hour']
        }
    
    def _determine_trend(self, current_aqi: int, final_aqi: int) -> str:
        """Détermine la tendance de la qualité de l'air"""
        diff = final_aqi - current_aqi
        if abs(diff) < 10:
            return "stable"
        elif diff < 0:
            return "improving"
        else:
            return "worsening"
    
    def _calculate_forecast_confidence(self, current_data: Dict) -> str:
        """Calcule le niveau de confiance des prédictions"""
        data_source = current_data.get('data_source', '')
        
        if 'OpenAQ' in data_source:
            return "High - Based on ground station measurements"
        elif 'NASA TEMPO' in data_source:
            return "Medium-High - Based on satellite observations"
        elif 'Estimation' in data_source:
            return "Medium - Based on regional models"
        else:
            return "Low - Limited data availability"
    
    def _calculate_historical_statistics(self, measurements: List[Dict], pollutant: Optional[str] = None) -> Dict:
        """Calcule les statistiques sur les données historiques"""
        if not measurements:
            return {"count": 0, "message": "No data available"}
        
        if pollutant and pollutant.lower() in measurements[0]:
            # Statistiques pour un polluant spécifique
            values = [m[pollutant.lower()] for m in measurements if pollutant.lower() in m]
            if values:
                return {
                    "count": len(measurements),
                    "pollutant": pollutant.lower(),
                    "average": round(sum(values) / len(values), 2),
                    "minimum": round(min(values), 2),
                    "maximum": round(max(values), 2),
                    "median": round(sorted(values)[len(values)//2], 2),
                    "std_deviation": round(self._calculate_std_dev(values), 2)
                }
        
        # Statistiques générales
        aqi_values = [m['aqi'] for m in measurements if 'aqi' in m]
        pm25_values = [m['pm25'] for m in measurements if 'pm25' in m]
        
        return {
            "count": len(measurements),
            "aqi": {
                "average": round(sum(aqi_values) / len(aqi_values), 1),
                "minimum": min(aqi_values),
                "maximum": max(aqi_values),
                "median": sorted(aqi_values)[len(aqi_values)//2]
            } if aqi_values else None,
            "pm25": {
                "average": round(sum(pm25_values) / len(pm25_values), 1),
                "minimum": round(min(pm25_values), 1),
                "maximum": round(max(pm25_values), 1),
                "median": round(sorted(pm25_values)[len(pm25_values)//2], 1)
            } if pm25_values else None
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calcule l'écart-type"""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _assess_data_quality(self, measurements: List[Dict]) -> str:
        """Évalue la qualité des données historiques"""
        if not measurements:
            return "No data"
        
        # Vérifier la complétude des données
        complete_measurements = sum(1 for m in measurements if all(
            key in m and m[key] is not None 
            for key in ['pm25', 'pm10', 'no2', 'aqi']
        ))
        
        completeness_ratio = complete_measurements / len(measurements)
        
        if completeness_ratio >= 0.9:
            return "High - Most measurements complete"
        elif completeness_ratio >= 0.7:
            return "Medium-High - Good data coverage"
        elif completeness_ratio >= 0.5:
            return "Medium - Partial data coverage"
        else:
            return "Low - Limited data coverage"
    
    def _get_data_sources_info(self, air_quality_data: Dict, weather_data: Dict) -> Dict:
        """Compile les informations sur les sources de données"""
        return {
            'air_quality': air_quality_data.get('data_source', 'Unknown'),
            'weather': weather_data.get('data_source', 'Unknown'),
            'integration': 'NASA TEMPO Air Quality API',
            'reliability': self._assess_source_reliability(air_quality_data.get('data_source', ''))
        }
    
    def _assess_source_reliability(self, source: str) -> str:
        """Évalue la fiabilité de la source de données"""
        if 'OpenAQ' in source:
            return "High - Ground-based measurements"
        elif 'NASA TEMPO' in source:
            return "High - Satellite observations"
        elif 'NOAA' in source:
            return "High - Official weather service"
        elif 'Estimation' in source:
            return "Medium - Model-based estimates"
        else:
            return "Variable - Mixed sources"
    
    def _get_health_recommendations(self, aqi: int) -> Dict:
        """Fournit des recommandations de santé basées sur l'AQI"""
        if aqi <= 50:
            return {
                "level": "Good",
                "color": "green",
                "message": "Air quality is satisfactory and poses little or no health risk",
                "activities": "Normal outdoor activities recommended for everyone",
                "sensitive_groups": "No restrictions"
            }
        elif aqi <= 100:
            return {
                "level": "Moderate",
                "color": "yellow", 
                "message": "Air quality is acceptable, but may be a concern for sensitive individuals",
                "activities": "Normal activities for most people; sensitive individuals should limit prolonged outdoor exertion",
                "sensitive_groups": "People with heart or lung disease, older adults, and children should limit prolonged outdoor exertion"
            }
        elif aqi <= 150:
            return {
                "level": "Unhealthy for Sensitive Groups",
                "color": "orange",
                "message": "Sensitive groups may experience health effects",
                "activities": "Reduce prolonged outdoor exertion, especially for sensitive groups",
                "sensitive_groups": "People with heart or lung disease, older adults, and children should avoid prolonged outdoor exertion"
            }
        elif aqi <= 200:
            return {
                "level": "Unhealthy",
                "color": "red",
                "message": "Everyone may begin to experience health effects",
                "activities": "Avoid prolonged outdoor exertion; everyone should reduce outdoor activities",
                "sensitive_groups": "People with heart or lung disease, older adults, and children should avoid outdoor activities"
            }
        elif aqi <= 300:
            return {
                "level": "Very Unhealthy",
                "color": "purple",
                "message": "Health warnings of emergency conditions",
                "activities": "Avoid all outdoor activities",
                "sensitive_groups": "Everyone should avoid all outdoor exertion"
            }
        else:
            return {
                "level": "Hazardous",
                "color": "maroon",
                "message": "Health alert - everyone may experience serious health effects",
                "activities": "Remain indoors and avoid all outdoor activities",
                "sensitive_groups": "Everyone should remain indoors with air filtration if possible"
            }
    
    # Méthodes de fallback
    async def _get_fallback_current_data(self, latitude: float, longitude: float) -> Dict:
        """Données de fallback pour les données actuelles"""
        # Utiliser le service de géolocalisation même en fallback
        try:
            async with geolocation_service as geo_service:
                location_name = await geo_service.get_enhanced_location_name(latitude, longitude)
                location_info = geo_service.get_location_info(latitude, longitude)
        except:
            location_name = f"Location {latitude:.3f}, {longitude:.3f}"
            location_info = {}
        
        return {
            'name': location_name,
            'coordinates': [latitude, longitude],
            'location_info': location_info,
            'aqi': 50,
            'pm25': 10.0,
            'pm10': 15.0,
            'no2': 15.0,
            'o3': 60.0,
            'so2': 5.0,
            'co': 1.0,
            'temperature': 20.0,
            'humidity': 60.0,
            'wind_speed': 5.0,
            'wind_direction': 'SW',
            'pressure': 1013.0,
            'visibility': 15.0,
            'data_source': 'Fallback Default Values',
            'last_updated': datetime.utcnow().isoformat() + "Z",
            'note': 'Default values used due to data source unavailability'
        }
    
    async def _get_fallback_forecast_data(self, latitude: float, longitude: float, hours: int) -> Dict:
        """Données de fallback pour les prédictions"""
        current_data = await self._get_fallback_current_data(latitude, longitude)
        forecast = self._generate_realistic_forecast(current_data, hours)
        
        return {
            'location': {
                'name': current_data['name'],
                'coordinates': [latitude, longitude]
            },
            'current': current_data,
            'forecast': forecast,
            'summary': self._calculate_forecast_summary(current_data, forecast),
            'health': self._get_health_recommendations(current_data['aqi']),
            'metadata': {
                'model': 'Fallback Forecast Model',
                'base_data_source': 'Default values',
                'confidence': 'Low - Limited data availability',
                'last_updated': datetime.now().isoformat() + "Z",
                'note': 'Fallback predictions due to data source issues'
            }
        }
    
    async def _get_fallback_historical_data(self, latitude: float, longitude: float, 
                                          start_date: datetime, end_date: datetime,
                                          pollutant: Optional[str] = None) -> Dict:
        """Données de fallback pour les données historiques"""
        # Utiliser le service de géolocalisation même en fallback
        try:
            async with geolocation_service as geo_service:
                location_name = await geo_service.get_enhanced_location_name(latitude, longitude)
                location_info = geo_service.get_location_info(latitude, longitude)
        except:
            location_name = f"Location {latitude:.3f}, {longitude:.3f}"
            location_info = {}
            
        # Générer des données basiques pour la période demandée
        measurements = []
        current_date = start_date
        
        while current_date <= end_date and len(measurements) < 1000:
            measurement = {
                'timestamp': current_date.isoformat() + "Z",
                'aqi': 50,
                'pm25': 10.0,
                'pm10': 15.0,
                'no2': 15.0,
                'o3': 60.0,
                'so2': 5.0,
                'co': 1.0
            }
            
            if pollutant and pollutant.lower() in measurement:
                filtered_measurement = {
                    'timestamp': measurement['timestamp'],
                    'aqi': measurement['aqi'],
                    pollutant.lower(): measurement[pollutant.lower()]
                }
                measurements.append(filtered_measurement)
            else:
                measurements.append(measurement)
            
            current_date += timedelta(hours=1)
        
        return {
            'location': {
                'name': location_name,
                'coordinates': [latitude, longitude],
                'location_info': location_info
            },
            'time_range': {
                'start_date': start_date.isoformat() + "Z",
                'end_date': end_date.isoformat() + "Z",
                'total_days': (end_date - start_date).days + 1,
                'data_points': len(measurements)
            },
            'measurements': measurements,
            'statistics': self._calculate_historical_statistics(measurements, pollutant),
            'metadata': {
                'pollutant_filter': pollutant if pollutant else 'all',
                'data_sources': ['Fallback Default Values'],
                'data_quality': 'Low - Default values only',
                'generated_at': datetime.now().isoformat() + "Z",
                'note': 'Fallback data due to source unavailability'
            }
        }
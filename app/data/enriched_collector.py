#!/usr/bin/env python3
"""
Collecteur enrichi avec APIs supplémentaires pour plus de données de polluants.
"""
import aiohttp
import asyncio
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnrichedAirQualityCollector:
    """Collecteur enrichi avec multiple APIs pour maximiser les données de polluants."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY", "ddd984279653ed94a82f3c9d667fa03f")
        self.epa_key = os.getenv("EPA_API_KEY")
        # Nouvelles clés API (à configurer dans .env)
        self.purpleair_key = os.getenv("PURPLEAIR_API_KEY")
        self.airvisual_key = os.getenv("AIRVISUAL_API_KEY")
        self.breezometer_key = os.getenv("BREEZOMETER_API_KEY")
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_comprehensive_pollution_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Récupère des données de pollution complètes de toutes les sources disponibles."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': {'latitude': latitude, 'longitude': longitude},
            'sources': {},
            'combined_pollutants': {},
            'data_quality_score': 0
        }
        
        # Collecte simultanée de toutes les sources
        tasks = [
            self._get_openweather_data(latitude, longitude),
            self._get_aqicn_detailed_data(latitude, longitude),
            self._get_purpleair_data(latitude, longitude),
            self._get_airvisual_data(latitude, longitude),
            self._get_breezometer_data(latitude, longitude),
            self._get_sensor_community_data(latitude, longitude),
        ]
        
        # Exécuter en parallèle pour optimiser la performance
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        source_names = ['openweather', 'aqicn', 'purpleair', 'airvisual', 'breezometer', 'sensor_community']
        
        for i, result in enumerate(source_results):
            if isinstance(result, dict) and result:
                source_name = source_names[i]
                results['sources'][source_name] = result
                logger.info(f"✅ {source_name}: {len(result.get('pollutants', {}))} polluants")
            elif isinstance(result, Exception):
                logger.warning(f"❌ {source_names[i]}: {result}")
        
        # Combiner et analyser les polluants
        results['combined_pollutants'] = self._combine_pollutant_data(results['sources'])
        results['data_quality_score'] = self._calculate_data_quality_score(results['sources'])
        results['primary_aqi'] = self._calculate_combined_aqi(results['combined_pollutants'])
        
        return results
    
    async def _get_openweather_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """OpenWeatherMap - Base de données fiable."""
        try:
            url = "http://api.openweathermap.org/data/2.5/air_pollution"
            params = {'lat': latitude, 'lon': longitude, 'appid': self.openweather_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'list' in data and data['list']:
                        pollution_data = data['list'][0]
                        components = pollution_data.get('components', {})
                        
                        return {
                            'aqi': self._convert_ow_aqi_to_us(pollution_data.get('main', {}).get('aqi', 3)),
                            'timestamp': datetime.fromtimestamp(pollution_data.get('dt', 0)).isoformat(),
                            'pollutants': {
                                'co': {'value': components.get('co'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'no': {'value': components.get('no'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'no2': {'value': components.get('no2'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'o3': {'value': components.get('o3'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'so2': {'value': components.get('so2'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'pm25': {'value': components.get('pm2_5'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'pm10': {'value': components.get('pm10'), 'unit': 'µg/m³', 'source': 'openweather'},
                                'nh3': {'value': components.get('nh3'), 'unit': 'µg/m³', 'source': 'openweather'}
                            },
                            'reliability': 0.9
                        }
        except Exception as e:
            logger.error(f"OpenWeather error: {e}")
            return {}
    
    async def _get_aqicn_detailed_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """AQICN - Données mondiales avec approche intelligente."""
        try:
            # Essayer d'abord les coordonnées exactes
            coords_data = await self._try_aqicn_coords(latitude, longitude)
            if coords_data:
                return coords_data
            
            # Sinon essayer par ville proche
            return await self._try_aqicn_nearest_city(latitude, longitude)
            
        except Exception as e:
            logger.error(f"AQICN error: {e}")
            return {}
    
    async def _try_aqicn_coords(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Essayer AQICN avec coordonnées exactes."""
        url = f"https://api.waqi.info/feed/geo:{latitude};{longitude}/?token=demo"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status') == 'ok' and 'data' in data:
                    return self._process_aqicn_data(data['data'])
        return {}
    
    async def _try_aqicn_nearest_city(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Essayer AQICN avec les villes les plus proches."""
        city_candidates = self._get_nearest_major_cities(latitude, longitude)
        
        for city in city_candidates:
            try:
                url = f"https://api.waqi.info/feed/{city}/?token=demo"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'ok' and 'data' in data:
                            result = self._process_aqicn_data(data['data'])
                            if result:
                                result['note'] = f"Data from nearest city: {city}"
                                return result
            except:
                continue
        return {}
    
    def _get_nearest_major_cities(self, latitude: float, longitude: float) -> List[str]:
        """Détermine les villes majeures les plus proches."""
        major_cities = {
            # Amérique du Nord
            'newyork': (40.7128, -74.0060),
            'losangeles': (34.0522, -118.2437),
            'chicago': (41.8781, -87.6298),
            'toronto': (43.6532, -79.3832),
            
            # Europe
            'paris': (48.8566, 2.3522),
            'london': (51.5074, -0.1278),
            'berlin': (52.5200, 13.4050),
            'madrid': (40.4168, -3.7038),
            
            # Asie
            'tokyo': (35.6762, 139.6503),
            'beijing': (39.9042, 116.4074),
            'shanghai': (31.2304, 121.4737),
            'singapore': (1.3521, 103.8198),
            
            # Océanie
            'sydney': (-33.8688, 151.2093),
            'melbourne': (-37.8136, 144.9631),
        }
        
        # Calculer distances et trier
        distances = []
        for city, (city_lat, city_lon) in major_cities.items():
            distance = ((latitude - city_lat) ** 2 + (longitude - city_lon) ** 2) ** 0.5
            distances.append((distance, city))
        
        distances.sort()
        return [city for _, city in distances[:3]]  # 3 villes les plus proches
    
    def _process_aqicn_data(self, waqi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite les données AQICN/WAQI."""
        if not waqi_data or waqi_data.get('aqi', -1) < 0:
            return {}
        
        result = {
            'aqi': waqi_data.get('aqi'),
            'station_name': waqi_data.get('city', {}).get('name', 'Unknown'),
            'timestamp': waqi_data.get('time', {}).get('iso'),
            'pollutants': {},
            'reliability': 0.8
        }
        
        # Extraire polluants
        iaqi = waqi_data.get('iaqi', {})
        pollutant_mapping = {
            'pm25': 'pm25', 'pm10': 'pm10', 'no2': 'no2', 'o3': 'o3', 
            'co': 'co', 'so2': 'so2', 't': 'temperature', 'h': 'humidity',
            'p': 'pressure', 'w': 'wind'
        }
        
        for waqi_key, our_key in pollutant_mapping.items():
            if waqi_key in iaqi:
                unit = 'µg/m³' if our_key in ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2'] else 'various'
                result['pollutants'][our_key] = {
                    'value': iaqi[waqi_key].get('v'),
                    'unit': unit,
                    'source': 'aqicn'
                }
        
        return result
    
    async def _get_purpleair_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """PurpleAir - Réseau de capteurs citoyens PM2.5/PM10."""
        if not self.purpleair_key:
            return {}
        
        try:
            url = "https://api.purpleair.com/v1/sensors"
            headers = {'X-API-Key': self.purpleair_key}
            params = {
                'fields': 'name,latitude,longitude,pm2.5_10minute,pm2.5_30minute,pm2.5_60minute,pm10.0_10minute',
                'location_type': '0',  # Extérieur seulement
                'nwlat': latitude + 0.1,
                'nwlng': longitude - 0.1,
                'selat': latitude - 0.1,
                'selng': longitude + 0.1,
                'max_age': 3600  # Données de moins d'1 heure
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and data['data']:
                        # Prendre le capteur le plus proche
                        sensors = data['data']
                        closest_sensor = min(sensors, key=lambda s: 
                            ((s[1] - latitude) ** 2 + (s[2] - longitude) ** 2) ** 0.5)
                        
                        return {
                            'sensor_name': closest_sensor[0],
                            'location': {'lat': closest_sensor[1], 'lon': closest_sensor[2]},
                            'pollutants': {
                                'pm25_10min': {'value': closest_sensor[3], 'unit': 'µg/m³', 'source': 'purpleair'},
                                'pm25_30min': {'value': closest_sensor[4], 'unit': 'µg/m³', 'source': 'purpleair'},
                                'pm25_60min': {'value': closest_sensor[5], 'unit': 'µg/m³', 'source': 'purpleair'},
                                'pm10_10min': {'value': closest_sensor[6], 'unit': 'µg/m³', 'source': 'purpleair'},
                            },
                            'reliability': 0.7  # Capteurs citoyens, fiabilité moindre
                        }
        except Exception as e:
            logger.error(f"PurpleAir error: {e}")
            return {}
    
    async def _get_airvisual_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """AirVisual (IQAir) - Données premium."""
        if not self.airvisual_key:
            return {}
        
        try:
            url = "https://api.airvisual.com/v2/nearest_city"
            params = {'lat': latitude, 'lon': longitude, 'key': self.airvisual_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success' and 'data' in data:
                        current = data['data']['current']
                        pollution = current.get('pollution', {})
                        
                        return {
                            'aqi': pollution.get('aqius'),  # AQI US
                            'city': data['data']['city'],
                            'country': data['data']['country'],
                            'pollutants': {
                                'pm25': {
                                    'value': pollution.get('p2', {}).get('conc'),
                                    'unit': 'µg/m³',
                                    'source': 'airvisual'
                                }
                            },
                            'weather': current.get('weather', {}),
                            'reliability': 0.95  # Données premium très fiables
                        }
        except Exception as e:
            logger.error(f"AirVisual error: {e}")
            return {}
    
    async def _get_breezometer_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Breezometer - API professionnelle."""
        if not self.breezometer_key:
            return {}
        
        try:
            url = "https://api.breezometer.com/air-quality/v2/current-conditions"
            params = {
                'lat': latitude, 'lon': longitude, 'key': self.breezometer_key,
                'features': 'breezometer_aqi,local_aqi,health_recommendations,sources_and_effects'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        aqi_data = data['data']
                        pollutants_data = aqi_data.get('pollutants', {})
                        
                        pollutants = {}
                        for pollutant, info in pollutants_data.items():
                            if 'concentration' in info:
                                pollutants[pollutant] = {
                                    'value': info['concentration']['value'],
                                    'unit': info['concentration']['units'],
                                    'source': 'breezometer'
                                }
                        
                        return {
                            'aqi': aqi_data.get('indexes', {}).get('baqi', {}).get('aqi'),
                            'pollutants': pollutants,
                            'health_recommendations': aqi_data.get('health_recommendations', {}),
                            'reliability': 0.9
                        }
        except Exception as e:
            logger.error(f"Breezometer error: {e}")
            return {}
    
    async def _get_sensor_community_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Sensor.Community (ex-Luftdaten) - Réseau européen de capteurs citoyens."""
        try:
            # API publique sensor.community
            url = "https://api.sensor.community/v1/sensor/"
            
            # Rechercher les capteurs dans un rayon
            bbox_size = 0.1  # ~10km
            sensors_url = f"https://maps.sensor.community/data/v2/data.dust.5min.json"
            
            async with self.session.get(sensors_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filtrer par proximité géographique
                    nearby_sensors = []
                    for sensor in data:
                        if 'location' in sensor:
                            sensor_lat = sensor['location']['latitude']
                            sensor_lon = sensor['location']['longitude']
                            
                            if (abs(sensor_lat - latitude) < bbox_size and 
                                abs(sensor_lon - longitude) < bbox_size):
                                nearby_sensors.append(sensor)
                    
                    if nearby_sensors:
                        # Prendre les données du capteur le plus proche
                        closest = min(nearby_sensors, key=lambda s: 
                            ((s['location']['latitude'] - latitude) ** 2 + 
                             (s['location']['longitude'] - longitude) ** 2) ** 0.5)
                        
                        pollutants = {}
                        for reading in closest.get('sensordatavalues', []):
                            value_type = reading.get('value_type')
                            value = reading.get('value')
                            
                            if value_type in ['P1', 'P2']:  # PM10, PM2.5
                                pollutant_name = 'pm10' if value_type == 'P1' else 'pm25'
                                pollutants[pollutant_name] = {
                                    'value': float(value),
                                    'unit': 'µg/m³',
                                    'source': 'sensor_community'
                                }
                        
                        return {
                            'sensor_id': closest.get('sensor', {}).get('id'),
                            'location': closest.get('location'),
                            'pollutants': pollutants,
                            'reliability': 0.6  # Capteurs citoyens
                        }
        except Exception as e:
            logger.error(f"Sensor.Community error: {e}")
            return {}
    
    def _combine_pollutant_data(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Combine les données de polluants de toutes les sources."""
        combined = {}
        
        for source_name, source_data in sources.items():
            pollutants = source_data.get('pollutants', {})
            reliability = source_data.get('reliability', 0.5)
            
            for pollutant, data in pollutants.items():
                if pollutant not in combined:
                    combined[pollutant] = {
                        'values': [],
                        'sources': [],
                        'weighted_average': None,
                        'confidence': 0
                    }
                
                value = data.get('value')
                if value is not None:
                    combined[pollutant]['values'].append({
                        'value': value,
                        'source': source_name,
                        'reliability': reliability,
                        'unit': data.get('unit', 'unknown')
                    })
                    combined[pollutant]['sources'].append(source_name)
        
        # Calculer moyennes pondérées
        for pollutant, data in combined.items():
            if data['values']:
                total_weighted = 0
                total_weight = 0
                
                for value_info in data['values']:
                    weight = value_info['reliability']
                    total_weighted += value_info['value'] * weight
                    total_weight += weight
                
                if total_weight > 0:
                    data['weighted_average'] = round(total_weighted / total_weight, 2)
                    data['confidence'] = min(total_weight, 1.0)
        
        return combined
    
    def _calculate_data_quality_score(self, sources: Dict[str, Any]) -> float:
        """Calcule un score de qualité des données basé sur le nombre et la fiabilité des sources."""
        if not sources:
            return 0.0
        
        total_reliability = sum(source.get('reliability', 0) for source in sources.values())
        source_count = len(sources)
        
        # Score basé sur la diversité et la fiabilité
        diversity_score = min(source_count / 5, 1.0)  # Max à 5 sources
        reliability_score = total_reliability / source_count if source_count > 0 else 0
        
        return round((diversity_score * 0.4 + reliability_score * 0.6), 2)
    
    def _calculate_combined_aqi(self, combined_pollutants: Dict[str, Any]) -> int:
        """Calcule un AQI combiné basé sur les polluants disponibles."""
        aqi_values = []
        
        # Calculer AQI pour chaque polluant majeur
        if 'pm25' in combined_pollutants and combined_pollutants['pm25']['weighted_average']:
            pm25 = combined_pollutants['pm25']['weighted_average']
            aqi_values.append(self._pm25_to_aqi(pm25))
        
        if 'pm10' in combined_pollutants and combined_pollutants['pm10']['weighted_average']:
            pm10 = combined_pollutants['pm10']['weighted_average']
            aqi_values.append(self._pm10_to_aqi(pm10))
        
        if 'no2' in combined_pollutants and combined_pollutants['no2']['weighted_average']:
            no2 = combined_pollutants['no2']['weighted_average']
            aqi_values.append(self._no2_to_aqi(no2))
        
        if 'o3' in combined_pollutants and combined_pollutants['o3']['weighted_average']:
            o3 = combined_pollutants['o3']['weighted_average']
            aqi_values.append(self._o3_to_aqi(o3))
        
        return max(aqi_values) if aqi_values else 50
    
    def _convert_ow_aqi_to_us(self, ow_aqi: int) -> int:
        """Convertit l'AQI OpenWeather (1-5) vers AQI US (0-500)."""
        conversion = {1: 25, 2: 60, 3: 100, 4: 175, 5: 350}
        return conversion.get(ow_aqi, 100)
    
    def _pm25_to_aqi(self, pm25: float) -> int:
        """Convertit PM2.5 en AQI selon EPA."""
        if pm25 <= 12.0:
            return int((50 / 12.0) * pm25)
        elif pm25 <= 35.4:
            return int(50 + ((100 - 50) / (35.4 - 12.1)) * (pm25 - 12.1))
        elif pm25 <= 55.4:
            return int(100 + ((150 - 100) / (55.4 - 35.5)) * (pm25 - 35.5))
        else:
            return min(500, int(150 + ((500 - 150) / (500 - 55.5)) * (pm25 - 55.5)))
    
    def _pm10_to_aqi(self, pm10: float) -> int:
        """Convertit PM10 en AQI selon EPA."""
        if pm10 <= 54:
            return int((50 / 54) * pm10)
        elif pm10 <= 154:
            return int(50 + ((100 - 50) / (154 - 55)) * (pm10 - 55))
        else:
            return min(500, int(100 + ((500 - 100) / (500 - 155)) * (pm10 - 155)))
    
    def _no2_to_aqi(self, no2: float) -> int:
        """Convertit NO2 (µg/m³) en AQI selon EPA."""
        no2_ppb = no2 * 0.532  # Conversion µg/m³ vers ppb
        if no2_ppb <= 53:
            return int((50 / 53) * no2_ppb)
        elif no2_ppb <= 100:
            return int(50 + ((100 - 50) / (100 - 54)) * (no2_ppb - 54))
        else:
            return min(500, int(100 + ((500 - 100) / (2000 - 101)) * (no2_ppb - 101)))
    
    def _o3_to_aqi(self, o3: float) -> int:
        """Convertit O3 (µg/m³) en AQI selon EPA."""
        o3_ppb = o3 * 0.51  # Conversion µg/m³ vers ppb
        if o3_ppb <= 54:
            return int((50 / 54) * o3_ppb)
        elif o3_ppb <= 70:
            return int(50 + ((100 - 50) / (70 - 55)) * (o3_ppb - 55))
        else:
            return min(500, int(100 + ((500 - 100) / (405 - 71)) * (o3_ppb - 71)))


# Instance globale
enriched_collector = EnrichedAirQualityCollector()
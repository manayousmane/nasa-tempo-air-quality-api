#!/usr/bin/env python3
"""
🏭 DATA PIPELINE POUR MODÈLES ML
================================================================================
Transforme les données d'API en features utilisables pour machine learning
================================================================================
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import sys
from pathlib import Path

sys.path.append('.')

from app.services.air_quality_service import AirQualityService
from app.core.logging import get_logger

logger = get_logger(__name__)

class AirQualityDataPipeline:
    """Pipeline de transformation des données air quality pour ML"""
    
    def __init__(self):
        self.air_service = AirQualityService()
        self.feature_columns = []
        self.target_columns = []
        
        # Configuration des polluants cibles
        self.target_pollutants = [
            'PM2.5', 'PM10', 'NO2', 'O3', 'CO', 'SO2'
        ]
        
        # Configuration des features météo
        self.weather_features = [
            'temperature', 'humidity', 'pressure', 'wind_speed', 
            'wind_direction', 'precipitation'
        ]
        
        # Configuration temporelle
        self.temporal_features = [
            'hour', 'day_of_week', 'month', 'season',
            'is_weekend', 'is_holiday'
        ]
        
        # Configuration géospatiale  
        self.spatial_features = [
            'latitude', 'longitude', 'elevation', 'population_density',
            'urban_index', 'industrial_index'
        ]
    
    async def collect_raw_data(self, 
                               locations: List[Tuple[float, float]], 
                               hours_back: int = 24) -> List[Dict]:
        """Collecte données brutes pour plusieurs locations"""
        logger.info(f"🔄 Collecte données pour {len(locations)} locations")
        
        collected_data = []
        
        for lat, lon in locations:
            try:
                logger.info(f"📍 Collecte: {lat}, {lon}")
                
                # Données actuelles
                current_data = await self.air_service.get_air_quality_indices(lat, lon)
                
                if current_data:
                    # Extraction des mesures individuelles
                    raw_measurements = await self._extract_raw_measurements(lat, lon)
                    
                    location_data = {
                        'latitude': lat,
                        'longitude': lon,
                        'timestamp': datetime.now(),
                        'current_data': current_data,
                        'raw_measurements': raw_measurements
                    }
                    
                    collected_data.append(location_data)
                    logger.info(f"✅ Données collectées: {lat}, {lon}")
                else:
                    logger.warning(f"⚠️ Aucune donnée: {lat}, {lon}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur collecte {lat}, {lon}: {str(e)}")
        
        logger.info(f"✅ Collecte terminée: {len(collected_data)}/{len(locations)}")
        return collected_data
    
    async def _extract_raw_measurements(self, lat: float, lon: float) -> Dict:
        """Extrait les mesures brutes des collecteurs"""
        try:
            # Utilisation directe des collecteurs pour données brutes
            from app.collectors.open_source_collectors import OpenSourceCollectors
            
            collectors = OpenSourceCollectors()
            raw_data = await collectors.collect_all_sources(lat, lon)
            
            measurements = {}
            
            for source_name, source_data in raw_data.items():
                if source_data and 'measurements' in source_data:
                    for measurement in source_data['measurements']:
                        pollutant = measurement.get('pollutant', '')
                        value = measurement.get('value')
                        unit = measurement.get('unit', '')
                        
                        if pollutant and value is not None:
                            measurements[f"{pollutant}_{source_name}"] = {
                                'value': float(value),
                                'unit': unit,
                                'source': source_name,
                                'timestamp': measurement.get('timestamp', datetime.now().isoformat())
                            }
            
            return measurements
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction mesures: {str(e)}")
            return {}
    
    def create_feature_matrix(self, raw_data: List[Dict]) -> pd.DataFrame:
        """Crée la matrice de features pour ML"""
        logger.info("🔧 Création matrice de features")
        
        features_list = []
        
        for location_data in raw_data:
            try:
                features = {}
                
                # Features de base
                features['latitude'] = location_data['latitude']
                features['longitude'] = location_data['longitude']
                features['timestamp'] = pd.to_datetime(location_data['timestamp'])
                
                # Features temporelles
                timestamp = location_data['timestamp']
                features.update(self._extract_temporal_features(timestamp))
                
                # Features géospatiales
                features.update(self._extract_spatial_features(
                    location_data['latitude'], 
                    location_data['longitude']
                ))
                
                # Features polluants (valeurs actuelles)
                if 'raw_measurements' in location_data:
                    features.update(self._extract_pollutant_features(
                        location_data['raw_measurements']
                    ))
                
                # Features météo (simulées pour l'instant)
                features.update(self._extract_weather_features(
                    location_data['latitude'], 
                    location_data['longitude']
                ))
                
                features_list.append(features)
                
            except Exception as e:
                logger.error(f"❌ Erreur création features: {str(e)}")
        
        df = pd.DataFrame(features_list)
        logger.info(f"✅ Matrice créée: {df.shape}")
        
        return df
    
    def _extract_temporal_features(self, timestamp: datetime) -> Dict:
        """Extrait les features temporelles"""
        return {
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'month': timestamp.month,
            'season': (timestamp.month % 12 + 3) // 3,  # 1=winter, 2=spring, etc.
            'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
            'is_holiday': 0,  # À implémenter avec calendrier des jours fériés
            'hour_sin': np.sin(2 * np.pi * timestamp.hour / 24),
            'hour_cos': np.cos(2 * np.pi * timestamp.hour / 24),
            'day_sin': np.sin(2 * np.pi * timestamp.weekday() / 7),
            'day_cos': np.cos(2 * np.pi * timestamp.weekday() / 7)
        }
    
    def _extract_spatial_features(self, lat: float, lon: float) -> Dict:
        """Extrait les features géospatiales"""
        # Approximations basiques - à améliorer avec vraies données géo
        return {
            'elevation': 0,  # À récupérer via API elevation
            'population_density': self._estimate_population_density(lat, lon),
            'urban_index': self._estimate_urban_index(lat, lon),
            'industrial_index': self._estimate_industrial_index(lat, lon),
            'distance_to_coast': self._estimate_distance_to_coast(lat, lon)
        }
    
    def _extract_pollutant_features(self, measurements: Dict) -> Dict:
        """Extrait les features des polluants"""
        features = {}
        
        for pollutant in self.target_pollutants:
            # Cherche toutes les sources pour ce polluant
            values = []
            for key, measurement in measurements.items():
                if pollutant in key:
                    values.append(measurement['value'])
            
            if values:
                features[f"{pollutant}_mean"] = np.mean(values)
                features[f"{pollutant}_std"] = np.std(values) if len(values) > 1 else 0
                features[f"{pollutant}_min"] = np.min(values)
                features[f"{pollutant}_max"] = np.max(values)
                features[f"{pollutant}_count"] = len(values)
            else:
                # Valeurs par défaut si pas de données
                features[f"{pollutant}_mean"] = np.nan
                features[f"{pollutant}_std"] = 0
                features[f"{pollutant}_min"] = np.nan
                features[f"{pollutant}_max"] = np.nan
                features[f"{pollutant}_count"] = 0
        
        return features
    
    def _extract_weather_features(self, lat: float, lon: float) -> Dict:
        """Extrait les features météo (simulées pour l'instant)"""
        # Simulation basique - à remplacer par vraie API météo
        import random
        random.seed(int(lat * lon * 1000))  # Seed déterministe
        
        return {
            'temperature': 15 + random.uniform(-10, 20),
            'humidity': 40 + random.uniform(0, 40),
            'pressure': 1013 + random.uniform(-20, 20),
            'wind_speed': random.uniform(0, 15),
            'wind_direction': random.uniform(0, 360),
            'precipitation': random.uniform(0, 10)
        }
    
    def _estimate_population_density(self, lat: float, lon: float) -> float:
        """Estime la densité de population (à améliorer)"""
        # Approximation basique basée sur les grandes villes
        major_cities = [
            (40.7128, -74.0060, 10000),  # NYC
            (34.0522, -118.2437, 8000),  # LA
            (48.8566, 2.3522, 9000),     # Paris
            (35.6762, 139.6503, 12000)   # Tokyo
        ]
        
        min_distance = float('inf')
        nearest_density = 1000  # Densité par défaut
        
        for city_lat, city_lon, density in major_cities:
            distance = np.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
            if distance < min_distance:
                min_distance = distance
                nearest_density = density
        
        # Décroissance avec la distance
        return max(100, nearest_density / (1 + min_distance * 100))
    
    def _estimate_urban_index(self, lat: float, lon: float) -> float:
        """Estime l'indice urbain"""
        return min(1.0, self._estimate_population_density(lat, lon) / 5000)
    
    def _estimate_industrial_index(self, lat: float, lon: float) -> float:
        """Estime l'indice industriel"""
        # Approximation basique
        return 0.3  # Valeur par défaut
    
    def _estimate_distance_to_coast(self, lat: float, lon: float) -> float:
        """Estime la distance à la côte"""
        # Approximation très basique
        return 100.0  # km par défaut
    
    def create_target_variables(self, raw_data: List[Dict], 
                                prediction_horizon: int = 1) -> pd.DataFrame:
        """Crée les variables cibles pour prédiction"""
        logger.info(f"🎯 Création variables cibles (horizon: {prediction_horizon}h)")
        
        targets_list = []
        
        for location_data in raw_data:
            targets = {}
            
            # Variables cibles: concentrations futures des polluants
            if 'raw_measurements' in location_data:
                measurements = location_data['raw_measurements']
                
                for pollutant in self.target_pollutants:
                    # Pour l'instant, on utilise les valeurs actuelles
                    # Dans un vrai pipeline, on aurait les valeurs futures
                    values = []
                    for key, measurement in measurements.items():
                        if pollutant in key:
                            values.append(measurement['value'])
                    
                    if values:
                        targets[f"{pollutant}_future"] = np.mean(values)
                    else:
                        targets[f"{pollutant}_future"] = np.nan
            
            # Variables cibles: AQI futur
            targets['aqi_future'] = 50  # Valeur simulée
            targets['health_risk_level'] = 1  # 0=low, 1=moderate, 2=high, 3=very_high
            
            targets_list.append(targets)
        
        df = pd.DataFrame(targets_list)
        logger.info(f"✅ Variables cibles créées: {df.shape}")
        
        return df
    
    def save_processed_data(self, features_df: pd.DataFrame, 
                           targets_df: pd.DataFrame, 
                           output_dir: str = "data/processed") -> Dict[str, str]:
        """Sauvegarde les données processées"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde features
        features_file = output_path / f"features_{timestamp}.csv"
        features_df.to_csv(features_file, index=False)
        
        # Sauvegarde targets
        targets_file = output_path / f"targets_{timestamp}.csv"
        targets_df.to_csv(targets_file, index=False)
        
        # Métadonnées
        metadata = {
            'timestamp': timestamp,
            'features_shape': features_df.shape,
            'targets_shape': targets_df.shape,
            'features_columns': list(features_df.columns),
            'targets_columns': list(targets_df.columns),
            'missing_values': {
                'features': features_df.isnull().sum().to_dict(),
                'targets': targets_df.isnull().sum().to_dict()
            }
        }
        
        metadata_file = output_path / f"metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"✅ Données sauvegardées:")
        logger.info(f"   Features: {features_file}")
        logger.info(f"   Targets: {targets_file}")
        logger.info(f"   Metadata: {metadata_file}")
        
        return {
            'features_file': str(features_file),
            'targets_file': str(targets_file),
            'metadata_file': str(metadata_file)
        }

async def main():
    """Pipeline principal de transformation des données"""
    print("🏭 PIPELINE DE TRANSFORMATION DES DONNÉES ML")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    pipeline = AirQualityDataPipeline()
    
    # Locations de test
    test_locations = [
        (40.7128, -74.0060),   # New York
        (34.0522, -118.2437),  # Los Angeles
        (48.8566, 2.3522),     # Paris
        (35.6762, 139.6503),   # Tokyo
        (51.5074, -0.1278),    # London
        (55.7558, 37.6173),    # Moscow
    ]
    
    try:
        # 1. Collecte des données brutes
        print("\n🔄 ÉTAPE 1: Collecte données brutes")
        raw_data = await pipeline.collect_raw_data(test_locations)
        
        if not raw_data:
            print("❌ Aucune donnée collectée")
            return
        
        # 2. Création matrice de features
        print("\n🔧 ÉTAPE 2: Création matrice de features")
        features_df = pipeline.create_feature_matrix(raw_data)
        
        # 3. Création variables cibles
        print("\n🎯 ÉTAPE 3: Création variables cibles")
        targets_df = pipeline.create_target_variables(raw_data)
        
        # 4. Sauvegarde
        print("\n💾 ÉTAPE 4: Sauvegarde données processées")
        files = pipeline.save_processed_data(features_df, targets_df)
        
        # 5. Résumé
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ PIPELINE ML")
        print("=" * 80)
        print(f"✅ Locations traitées: {len(raw_data)}")
        print(f"✅ Features créées: {features_df.shape[1]}")
        print(f"✅ Targets créées: {targets_df.shape[1]}")
        print(f"✅ Échantillons: {features_df.shape[0]}")
        
        print(f"\n📈 Features principales:")
        for col in features_df.columns[:10]:  # Premiers 10
            print(f"   • {col}")
        
        print(f"\n🎯 Variables cibles:")
        for col in targets_df.columns:
            print(f"   • {col}")
        
        print(f"\n💾 Fichiers générés:")
        for key, file_path in files.items():
            print(f"   • {key}: {file_path}")
        
        print("\n🎉 PIPELINE ML PRÊT!")
        print("🔄 Prochaines étapes: Entraînement des modèles")
        
    except Exception as e:
        print(f"❌ Erreur pipeline: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
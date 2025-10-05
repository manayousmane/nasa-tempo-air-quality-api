#!/usr/bin/env python3
"""
🛰️ PIPELINE DONNÉES TEMPO AMÉRIQUE DU NORD
================================================================================
Pipeline spécialisé pour collecte historique et prédictions TEMPO
Zone couverte: 40°N-70°N, 70°W-130°W (Amérique du Nord)
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
import random
from dataclasses import dataclass

sys.path.append('.')

from app.services.air_quality_service import AirQualityService
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class TempoDataPoint:
    """Point de données TEMPO avec coordonnées et historique"""
    latitude: float
    longitude: float
    timestamp: datetime
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    co: Optional[float] = None
    so2: Optional[float] = None
    
    # Features météo
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    
    # Features géographiques
    elevation: Optional[float] = None
    population_density: Optional[float] = None
    urban_index: Optional[float] = None
    land_use_type: Optional[str] = None
    
    # Features temporelles (calculées)
    hour: Optional[int] = None
    day_of_week: Optional[int] = None
    month: Optional[int] = None
    season: Optional[int] = None
    is_weekend: Optional[bool] = None

class TempoNorthAmericaPipeline:
    """Pipeline spécialisé pour données TEMPO Amérique du Nord"""
    
    def __init__(self):
        self.air_service = AirQualityService()
        
        # Zone de couverture TEMPO (Amérique du Nord)
        self.coverage_bounds = {
            'lat_min': 40.0,   # 40°N (sud des USA)
            'lat_max': 70.0,   # 70°N (nord du Canada)
            'lon_min': -130.0, # 130°W (côte ouest)
            'lon_max': -70.0   # 70°W (côte est)
        }
        
        # Grille de points de référence pour l'Amérique du Nord
        self.reference_grid = self._create_reference_grid()
        
        # Configuration temporelle pour historique
        self.historical_days = 90  # 3 mois d'historique
        self.prediction_horizons = [1, 3, 6, 12, 24]  # heures
        
    def _create_reference_grid(self) -> List[Tuple[float, float]]:
        """Crée une grille de points de référence pour l'Amérique du Nord"""
        grid_points = []
        
        # Grandes villes d'Amérique du Nord (points d'ancrage)
        major_cities = [
            # USA
            (40.7128, -74.0060),   # New York
            (34.0522, -118.2437),  # Los Angeles
            (41.8781, -87.6298),   # Chicago
            (29.7604, -95.3698),   # Houston
            (33.4484, -112.0740),  # Phoenix
            (39.9526, -75.1652),   # Philadelphia
            (32.7767, -96.7970),   # Dallas
            (37.7749, -122.4194),  # San Francisco
            (47.6062, -122.3321),  # Seattle
            (25.7617, -80.1918),   # Miami
            
            # Canada
            (43.6532, -79.3832),   # Toronto
            (45.5017, -73.5673),   # Montréal
            (49.2827, -123.1207),  # Vancouver
            (51.0447, -114.0719),  # Calgary
            (53.5461, -113.4938),  # Edmonton
            (45.4215, -75.6972),   # Ottawa
            (46.8139, -71.2080),   # Québec
            (49.8951, -97.1384),   # Winnipeg
            
            # Mexique (partie nord)
            (25.6866, -100.3161),  # Monterrey
            (32.6519, -115.5410),  # Tijuana
        ]
        
        grid_points.extend(major_cities)
        
        # Grille systématique sur la zone TEMPO
        lat_step = 2.0  # Pas de 2 degrés
        lon_step = 2.0
        
        for lat in np.arange(self.coverage_bounds['lat_min'], 
                           self.coverage_bounds['lat_max'], lat_step):
            for lon in np.arange(self.coverage_bounds['lon_min'], 
                               self.coverage_bounds['lon_max'], lon_step):
                grid_points.append((lat, lon))
        
        logger.info(f"📍 Grille créée: {len(grid_points)} points de référence")
        return grid_points
    
    def is_in_tempo_coverage(self, lat: float, lon: float) -> bool:
        """Vérifie si les coordonnées sont dans la zone TEMPO"""
        return (self.coverage_bounds['lat_min'] <= lat <= self.coverage_bounds['lat_max'] and
                self.coverage_bounds['lon_min'] <= lon <= self.coverage_bounds['lon_max'])
    
    async def collect_historical_data(self, days_back: int = 90) -> List[TempoDataPoint]:
        """Collecte des données historiques simulées pour l'entraînement"""
        logger.info(f"🕐 Collecte historique: {days_back} jours sur {len(self.reference_grid)} points")
        
        historical_data = []
        
        # Simulation d'historique pour chaque point de la grille
        for lat, lon in self.reference_grid:
            if not self.is_in_tempo_coverage(lat, lon):
                continue
                
            # Génération de données historiques pour ce point
            for day_offset in range(days_back):
                timestamp = datetime.now() - timedelta(days=day_offset)
                
                # Simulation de 4 mesures par jour (6h, 12h, 18h, 24h)
                for hour in [6, 12, 18, 24]:
                    point_timestamp = timestamp.replace(hour=hour % 24, minute=0, second=0)
                    
                    data_point = await self._simulate_historical_point(lat, lon, point_timestamp)
                    historical_data.append(data_point)
        
        logger.info(f"✅ Données historiques collectées: {len(historical_data)} points")
        return historical_data
    
    async def _simulate_historical_point(self, lat: float, lon: float, 
                                       timestamp: datetime) -> TempoDataPoint:
        """Simule un point de données historiques réaliste"""
        # Seed basé sur coordonnées et temps pour consistance
        seed = int((lat * 1000 + lon * 1000 + timestamp.timestamp()) % 1000000)
        random.seed(seed)
        np.random.seed(seed % 1000)
        
        # Patterns temporels réalistes
        hour_factor = 1.0 + 0.3 * np.sin(2 * np.pi * timestamp.hour / 24)
        seasonal_factor = 1.0 + 0.2 * np.sin(2 * np.pi * timestamp.month / 12)
        
        # Patterns géographiques (pollution plus élevée près des villes)
        urban_factor = self._calculate_urban_factor(lat, lon)
        
        # Simulation polluants avec patterns réalistes
        base_pm25 = 10 + random.uniform(0, 15) * urban_factor * hour_factor * seasonal_factor
        base_pm10 = base_pm25 * 1.5 + random.uniform(0, 10)
        base_no2 = 15 + random.uniform(0, 20) * urban_factor * hour_factor
        base_o3 = 40 + random.uniform(-10, 20) * (1/hour_factor)  # O3 inverse au trafic
        base_co = 0.5 + random.uniform(0, 1.0) * urban_factor
        base_so2 = 2 + random.uniform(0, 5) * urban_factor
        
        # Simulation météo
        temp_base = 10 + 20 * np.sin(2 * np.pi * timestamp.month / 12)  # Saisonnier
        temp_daily = 5 * np.sin(2 * np.pi * (timestamp.hour - 6) / 24)  # Cycle journalier
        
        return TempoDataPoint(
            latitude=lat,
            longitude=lon,
            timestamp=timestamp,
            pm25=max(0, base_pm25 + random.gauss(0, 2)),
            pm10=max(0, base_pm10 + random.gauss(0, 3)),
            no2=max(0, base_no2 + random.gauss(0, 3)),
            o3=max(0, base_o3 + random.gauss(0, 5)),
            co=max(0, base_co + random.gauss(0, 0.1)),
            so2=max(0, base_so2 + random.gauss(0, 1)),
            
            # Météo
            temperature=temp_base + temp_daily + random.gauss(0, 3),
            humidity=50 + random.uniform(-20, 30),
            pressure=1013 + random.gauss(0, 10),
            wind_speed=random.uniform(0, 15),
            wind_direction=random.uniform(0, 360),
            
            # Géographie
            elevation=self._estimate_elevation(lat, lon),
            population_density=self._estimate_population_density(lat, lon),
            urban_index=urban_factor,
            land_use_type=self._estimate_land_use(lat, lon),
            
            # Temporel
            hour=timestamp.hour,
            day_of_week=timestamp.weekday(),
            month=timestamp.month,
            season=(timestamp.month % 12 + 3) // 3,
            is_weekend=timestamp.weekday() >= 5
        )
    
    def _calculate_urban_factor(self, lat: float, lon: float) -> float:
        """Calcule facteur urbain basé sur proximité aux villes"""
        major_cities = [
            (40.7128, -74.0060, 3.0),   # NYC - facteur élevé
            (34.0522, -118.2437, 2.5),  # LA
            (41.8781, -87.6298, 2.0),   # Chicago
            (29.7604, -95.3698, 1.8),   # Houston
            (43.6532, -79.3832, 2.0),   # Toronto
        ]
        
        min_distance = float('inf')
        max_factor = 1.0
        
        for city_lat, city_lon, factor in major_cities:
            distance = np.sqrt((lat - city_lat)**2 + (lon - city_lon)**2)
            if distance < min_distance:
                min_distance = distance
                max_factor = factor
        
        # Décroissance exponentielle avec la distance
        return max(1.0, max_factor * np.exp(-min_distance / 2.0))
    
    def _estimate_elevation(self, lat: float, lon: float) -> float:
        """Estime l'élévation (approximation)"""
        # Montagnes Rocheuses
        if -115 <= lon <= -105 and 40 <= lat <= 50:
            return 1000 + random.uniform(0, 2000)
        # Appalaches
        elif -85 <= lon <= -75 and 35 <= lat <= 45:
            return 500 + random.uniform(0, 1000)
        # Plaines
        else:
            return random.uniform(0, 500)
    
    def _estimate_population_density(self, lat: float, lon: float) -> float:
        """Estime densité de population"""
        return max(10, self._calculate_urban_factor(lat, lon) * 1000)
    
    def _estimate_land_use(self, lat: float, lon: float) -> str:
        """Estime le type d'utilisation du sol"""
        urban_factor = self._calculate_urban_factor(lat, lon)
        if urban_factor > 2.0:
            return "urban"
        elif urban_factor > 1.5:
            return "suburban"
        elif lat > 55:  # Nord du Canada
            return "forest"
        else:
            return "rural"
    
    def create_ml_dataset(self, historical_data: List[TempoDataPoint]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Crée dataset ML avec features et targets pour prédiction"""
        logger.info(f"🔧 Création dataset ML à partir de {len(historical_data)} points")
        
        # Conversion en DataFrame
        data_records = []
        for point in historical_data:
            record = {
                # Coordonnées
                'latitude': point.latitude,
                'longitude': point.longitude,
                
                # Temporel
                'hour': point.hour,
                'day_of_week': point.day_of_week,
                'month': point.month,
                'season': point.season,
                'is_weekend': int(point.is_weekend),
                'hour_sin': np.sin(2 * np.pi * point.hour / 24),
                'hour_cos': np.cos(2 * np.pi * point.hour / 24),
                'day_sin': np.sin(2 * np.pi * point.day_of_week / 7),
                'day_cos': np.cos(2 * np.pi * point.day_of_week / 7),
                'month_sin': np.sin(2 * np.pi * point.month / 12),
                'month_cos': np.cos(2 * np.pi * point.month / 12),
                
                # Météo
                'temperature': point.temperature,
                'humidity': point.humidity,
                'pressure': point.pressure,
                'wind_speed': point.wind_speed,
                'wind_direction': point.wind_direction,
                'wind_u': point.wind_speed * np.cos(np.radians(point.wind_direction)),
                'wind_v': point.wind_speed * np.sin(np.radians(point.wind_direction)),
                
                # Géographie
                'elevation': point.elevation,
                'population_density': point.population_density,
                'urban_index': point.urban_index,
                'land_use_urban': 1 if point.land_use_type == 'urban' else 0,
                'land_use_suburban': 1 if point.land_use_type == 'suburban' else 0,
                'land_use_rural': 1 if point.land_use_type == 'rural' else 0,
                'land_use_forest': 1 if point.land_use_type == 'forest' else 0,
                
                # Polluants actuels (features)
                'pm25_current': point.pm25,
                'pm10_current': point.pm10,
                'no2_current': point.no2,
                'o3_current': point.o3,
                'co_current': point.co,
                'so2_current': point.so2,
                
                # Targets (à calculer avec décalage temporel)
                'pm25_target': point.pm25,  # Sera recalculé
                'pm10_target': point.pm10,
                'no2_target': point.no2,
                'o3_target': point.o3,
                'co_target': point.co,
                'so2_target': point.so2,
                
                'timestamp': point.timestamp
            }
            data_records.append(record)
        
        df = pd.DataFrame(data_records)
        df = df.sort_values(['latitude', 'longitude', 'timestamp'])
        
        # Création des targets avec décalage temporel (prédiction)
        df = self._create_prediction_targets(df)
        
        # Séparation features et targets
        feature_columns = [col for col in df.columns 
                          if not col.endswith('_target') and col != 'timestamp']
        target_columns = [col for col in df.columns if col.endswith('_target')]
        
        features_df = df[feature_columns].copy()
        targets_df = df[target_columns].copy()
        
        # Nettoyage des valeurs manquantes
        features_df = features_df.dropna()
        targets_df = targets_df.dropna()
        
        logger.info(f"✅ Dataset créé: Features{features_df.shape}, Targets{targets_df.shape}")
        return features_df, targets_df
    
    def _create_prediction_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crée les variables cibles avec décalage temporel"""
        logger.info("🎯 Création targets avec décalage temporel")
        
        # Grouper par location
        for (lat, lon), group in df.groupby(['latitude', 'longitude']):
            group = group.sort_values('timestamp')
            
            # Décalage de 3h pour prédiction
            shift_hours = 3
            
            for pollutant in ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2']:
                current_col = f'{pollutant}_current'
                target_col = f'{pollutant}_target'
                
                if current_col in group.columns:
                    # Décalage vers l'avant (valeur future)
                    future_values = group[current_col].shift(-shift_hours)
                    df.loc[group.index, target_col] = future_values
        
        return df
    
    def save_tempo_dataset(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, 
                          output_dir: str = "data/tempo_north_america") -> Dict[str, str]:
        """Sauvegarde le dataset TEMPO spécialisé"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde
        features_file = output_path / f"tempo_features_{timestamp}.csv"
        targets_file = output_path / f"tempo_targets_{timestamp}.csv"
        
        features_df.to_csv(features_file, index=False)
        targets_df.to_csv(targets_file, index=False)
        
        # Métadonnées spécialisées
        metadata = {
            'timestamp': timestamp,
            'dataset_type': 'TEMPO_North_America',
            'coverage_area': self.coverage_bounds,
            'features_shape': features_df.shape,
            'targets_shape': targets_df.shape,
            'temporal_resolution': '6_hours',
            'historical_days': self.historical_days,
            'grid_points': len(self.reference_grid),
            'prediction_horizons_hours': self.prediction_horizons,
            'features_columns': list(features_df.columns),
            'targets_columns': list(targets_df.columns),
            'coverage_validation': {
                'lat_range': [features_df['latitude'].min(), features_df['latitude'].max()],
                'lon_range': [features_df['longitude'].min(), features_df['longitude'].max()],
                'total_locations': features_df[['latitude', 'longitude']].drop_duplicates().shape[0]
            }
        }
        
        metadata_file = output_path / f"tempo_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"✅ Dataset TEMPO sauvegardé:")
        logger.info(f"   Features: {features_file}")
        logger.info(f"   Targets: {targets_file}")
        logger.info(f"   Metadata: {metadata_file}")
        
        return {
            'features_file': str(features_file),
            'targets_file': str(targets_file),
            'metadata_file': str(metadata_file)
        }

async def main():
    """Pipeline principal TEMPO Amérique du Nord"""
    print("🛰️ PIPELINE TEMPO AMÉRIQUE DU NORD")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Zone: 40°N-70°N, 70°W-130°W (TEMPO coverage)")
    print("=" * 80)
    
    pipeline = TempoNorthAmericaPipeline()
    
    try:
        # 1. Collecte historique
        print("\n🕐 ÉTAPE 1: Collecte données historiques TEMPO")
        historical_data = await pipeline.collect_historical_data(days_back=30)  # 1 mois pour test
        
        if not historical_data:
            print("❌ Aucune donnée historique collectée")
            return
        
        # 2. Création dataset ML
        print("\n🔧 ÉTAPE 2: Création dataset ML spécialisé")
        features_df, targets_df = pipeline.create_ml_dataset(historical_data)
        
        # 3. Sauvegarde
        print("\n💾 ÉTAPE 3: Sauvegarde dataset TEMPO")
        files = pipeline.save_tempo_dataset(features_df, targets_df)
        
        # 4. Résumé
        print("\n" + "=" * 80)
        print("🎉 DATASET TEMPO AMÉRIQUE DU NORD CRÉÉ!")
        print("=" * 80)
        
        print(f"✅ Points historiques: {len(historical_data)}")
        print(f"✅ Features: {features_df.shape[1]} colonnes")
        print(f"✅ Targets: {targets_df.shape[1]} polluants")
        print(f"✅ Échantillons: {features_df.shape[0]}")
        print(f"✅ Locations couvertes: {features_df[['latitude', 'longitude']].drop_duplicates().shape[0]}")
        
        coverage = features_df[['latitude', 'longitude']].agg(['min', 'max'])
        print(f"\n📍 Couverture géographique:")
        print(f"   Latitude: {coverage.loc['min', 'latitude']:.1f}° - {coverage.loc['max', 'latitude']:.1f}°")
        print(f"   Longitude: {coverage.loc['min', 'longitude']:.1f}° - {coverage.loc['max', 'longitude']:.1f}°")
        
        print(f"\n🎯 Variables prédites:")
        for col in targets_df.columns:
            print(f"   • {col}")
        
        print(f"\n📁 Fichiers générés:")
        for key, file_path in files.items():
            print(f"   • {key}: {file_path}")
        
        print(f"\n🔄 Prochaines étapes:")
        print(f"   • Entraîner modèles spécialisés TEMPO")
        print(f"   • Créer API de prédiction géographique")
        print(f"   • Intégrer avec données satellites réelles")
        
    except Exception as e:
        print(f"❌ Erreur pipeline TEMPO: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
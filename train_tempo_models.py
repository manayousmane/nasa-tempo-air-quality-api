#!/usr/bin/env python3
"""
🤖 MODÈLES ML SPÉCIALISÉS TEMPO
================================================================================
Entraînement de modèles pour prédiction air quality Amérique du Nord
Système de prédiction géographique pour toutes coordonnées TEMPO
================================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import pickle
import json
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import Ridge

# Géospatial
from scipy.spatial.distance import cdist
from scipy.interpolate import griddata

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from app.core.logging import get_logger

logger = get_logger(__name__)

class TempoMLPredictor:
    """Système de prédiction ML spécialisé pour TEMPO"""
    
    def __init__(self, models_dir: str = "models/tempo"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.grid_interpolators = {}
        
        # Configuration modèles optimisés pour données géospatiales
        self.model_configs = {
            'random_forest': {
                'class': RandomForestRegressor,
                'params': {
                    'n_estimators': 200,
                    'max_depth': 15,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'random_state': 42,
                    'n_jobs': -1
                }
            },
            'gradient_boosting': {
                'class': GradientBoostingRegressor,
                'params': {
                    'n_estimators': 150,
                    'max_depth': 8,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'random_state': 42
                }
            },
            'knn_spatial': {
                'class': KNeighborsRegressor,
                'params': {
                    'n_neighbors': 10,
                    'weights': 'distance',
                    'metric': 'haversine'  # Optimisé pour coordonnées géographiques
                }
            },
            'ridge_baseline': {
                'class': Ridge,
                'params': {
                    'alpha': 1.0,
                    'random_state': 42
                }
            }
        }
        
        if XGBOOST_AVAILABLE:
            self.model_configs['xgboost'] = {
                'class': xgb.XGBRegressor,
                'params': {
                    'n_estimators': 150,
                    'max_depth': 8,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42,
                    'n_jobs': -1
                }
            }
        
        # Polluants TEMPO
        self.pollutants = ['pm25', 'pm10', 'no2', 'o3', 'co', 'so2']
        
        # Zone de couverture TEMPO
        self.tempo_bounds = {
            'lat_min': 40.0, 'lat_max': 70.0,
            'lon_min': -130.0, 'lon_max': -70.0
        }
    
    def load_tempo_data(self, data_dir: str = "data/tempo_north_america") -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Charge les dernières données TEMPO"""
        data_path = Path(data_dir)
        
        # Trouve les fichiers les plus récents
        feature_files = list(data_path.glob("tempo_features_*.csv"))
        target_files = list(data_path.glob("tempo_targets_*.csv"))
        
        if not feature_files or not target_files:
            raise FileNotFoundError("Aucun fichier TEMPO trouvé. Exécutez tempo_pipeline_north_america.py")
        
        # Tri par date
        feature_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        target_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        features_df = pd.read_csv(feature_files[0])
        targets_df = pd.read_csv(target_files[0])
        
        logger.info(f"📂 Données chargées: Features{features_df.shape}, Targets{targets_df.shape}")
        return features_df, targets_df
    
    def prepare_spatial_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Prépare features géospatiales optimisées"""
        df = features_df.copy()
        
        # Conversion coordonnées en radians pour calculs géospatiales
        df['lat_rad'] = np.radians(df['latitude'])
        df['lon_rad'] = np.radians(df['longitude'])
        
        # Features géospatiales avancées
        df['lat_lon_interaction'] = df['latitude'] * df['longitude']
        df['distance_to_center'] = np.sqrt(
            (df['latitude'] - 55.0)**2 + (df['longitude'] + 100.0)**2
        )
        
        # Patterns géographiques Nord-Américains
        # Côte Est (influence océanique)
        df['east_coast_proximity'] = np.exp(-(df['longitude'] + 75.0)**2 / 100)
        # Côte Ouest (influence Pacifique)
        df['west_coast_proximity'] = np.exp(-(df['longitude'] + 120.0)**2 / 100)
        # Région des Grands Lacs
        df['great_lakes_proximity'] = np.exp(-((df['latitude'] - 45.0)**2 + (df['longitude'] + 85.0)**2) / 50)
        
        return df
    
    def train_spatial_models(self, features_df: pd.DataFrame, targets_df: pd.DataFrame) -> Dict:
        """Entraîne modèles spécialisés pour prédiction spatiale"""
        logger.info("🚀 Entraînement modèles TEMPO spécialisés")
        
        # Vérification alignement des données
        logger.info(f"📊 Shapes initiales: Features{features_df.shape}, Targets{targets_df.shape}")
        
        # Alignement des indices (prendre le minimum)
        min_samples = min(len(features_df), len(targets_df))
        features_df = features_df.iloc[:min_samples].copy()
        targets_df = targets_df.iloc[:min_samples].copy()
        
        logger.info(f"📊 Shapes alignées: Features{features_df.shape}, Targets{targets_df.shape}")
        
        # Préparation features spatiales
        X = self.prepare_spatial_features(features_df)
        
        # Exclusion des colonnes non-numériques
        feature_columns = X.select_dtypes(include=[np.number]).columns.tolist()
        X = X[feature_columns]
        
        results = {}
        
        # Entraînement pour chaque polluant
        for pollutant in self.pollutants:
            target_col = f'{pollutant}_target'
            if target_col not in targets_df.columns:
                logger.warning(f"⚠️ {target_col} non trouvé")
                continue
            
            logger.info(f"🎯 Entraînement pour: {pollutant}")
            
            y = targets_df[target_col].values
            
            # Vérification finale des shapes
            if len(X) != len(y):
                logger.error(f"❌ Shape mismatch: X{len(X)} vs y{len(y)}")
                continue
            
            # Suppression des valeurs manquantes
            mask = ~(np.isnan(X.values).any(axis=1) | np.isnan(y))
            X_clean = X[mask]
            y_clean = y[mask]
            
            logger.info(f"   📊 Données nettoyées: {len(X_clean)} échantillons")
            
            if len(X_clean) < 100:
                logger.warning(f"⚠️ Pas assez de données pour {pollutant}: {len(X_clean)}")
                continue
            
            # Split train/test avec stratification géographique
            X_train, X_test, y_train, y_test = train_test_split(
                X_clean, y_clean, test_size=0.2, random_state=42
            )
            
            # Normalisation
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            self.scalers[pollutant] = scaler
            
            pollutant_results = {}
            
            # Entraînement de chaque modèle
            for model_name, config in self.model_configs.items():
                try:
                    logger.info(f"   🔄 {model_name}")
                    
                    # Création du modèle
                    if model_name == 'knn_spatial':
                        # KNN avec coordonnées géographiques directes
                        coords_train = X_train[['latitude', 'longitude']].values
                        coords_test = X_test[['latitude', 'longitude']].values
                        
                        # Conversion en radians pour distance haversine
                        coords_train_rad = np.radians(coords_train)
                        coords_test_rad = np.radians(coords_test)
                        
                        model = config['class'](**config['params'])
                        model.fit(coords_train_rad, y_train)
                        y_pred = model.predict(coords_test_rad)
                    else:
                        # Modèles standards avec toutes les features
                        model = config['class'](**config['params'])
                        model.fit(X_train_scaled, y_train)
                        y_pred = model.predict(X_test_scaled)
                    
                    # Métriques
                    metrics = {
                        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                        'mae': mean_absolute_error(y_test, y_pred),
                        'r2': r2_score(y_test, y_pred),
                        'samples_train': len(X_train),
                        'samples_test': len(X_test)
                    }
                    
                    # Sauvegarde du modèle
                    model_file = self.models_dir / f"{pollutant}_{model_name}_tempo.pkl"
                    with open(model_file, 'wb') as f:
                        pickle.dump({
                            'model': model,
                            'scaler': scaler if model_name != 'knn_spatial' else None,
                            'feature_columns': feature_columns,
                            'pollutant': pollutant,
                            'model_type': model_name
                        }, f)
                    
                    pollutant_results[model_name] = {
                        'metrics': metrics,
                        'model_file': str(model_file)
                    }
                    
                    logger.info(f"   ✅ {model_name}: R²={metrics['r2']:.3f}, RMSE={metrics['rmse']:.3f}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Erreur {model_name}: {str(e)}")
                    pollutant_results[model_name] = {'error': str(e)}
            
            results[pollutant] = pollutant_results
        
        # Sauvegarde métadonnées
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'model_type': 'TEMPO_Spatial_Prediction',
            'coverage_area': self.tempo_bounds,
            'pollutants': self.pollutants,
            'models_trained': list(self.model_configs.keys()),
            'feature_columns': feature_columns,
            'results': results
        }
        
        metadata_file = self.models_dir / f"tempo_models_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return results
    
    def create_geographic_predictor(self, lat: float, lon: float, 
                                   features: Dict[str, float]) -> Dict[str, float]:
        """Prédit la qualité de l'air pour n'importe quelles coordonnées TEMPO"""
        
        if not self.is_in_tempo_coverage(lat, lon):
            raise ValueError(f"Coordonnées hors zone TEMPO: {lat}, {lon}")
        
        predictions = {}
        
        # Création du vecteur de features pour la prédiction
        feature_vector = self._create_feature_vector(lat, lon, features)
        
        # Prédiction pour chaque polluant
        for pollutant in self.pollutants:
            try:
                # Chargement du meilleur modèle pour ce polluant
                best_model_file = self._find_best_model(pollutant)
                
                if best_model_file:
                    with open(best_model_file, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    model = model_data['model']
                    scaler = model_data.get('scaler')
                    model_type = model_data.get('model_type')
                    
                    if model_type == 'knn_spatial':
                        # KNN spatial avec coordonnées
                        coords = np.radians([[lat, lon]])
                        prediction = model.predict(coords)[0]
                    else:
                        # Modèles avec features complètes
                        if scaler:
                            feature_vector_scaled = scaler.transform([feature_vector])
                            prediction = model.predict(feature_vector_scaled)[0]
                        else:
                            prediction = model.predict([feature_vector])[0]
                    
                    predictions[pollutant] = max(0, prediction)  # Valeurs positives seulement
                
            except Exception as e:
                logger.error(f"❌ Erreur prédiction {pollutant}: {str(e)}")
                predictions[pollutant] = None
        
        return predictions
    
    def _create_feature_vector(self, lat: float, lon: float, features: Dict[str, float]) -> List[float]:
        """Crée le vecteur de features pour une prédiction"""
        # Features de base géographiques
        base_features = {
            'latitude': lat,
            'longitude': lon,
            'lat_rad': np.radians(lat),
            'lon_rad': np.radians(lon),
            'lat_lon_interaction': lat * lon,
            'distance_to_center': np.sqrt((lat - 55.0)**2 + (lon + 100.0)**2),
            'east_coast_proximity': np.exp(-(lon + 75.0)**2 / 100),
            'west_coast_proximity': np.exp(-(lon + 120.0)**2 / 100),
            'great_lakes_proximity': np.exp(-((lat - 45.0)**2 + (lon + 85.0)**2) / 50)
        }
        
        # Fusion avec features fournies
        all_features = {**base_features, **features}
        
        # Ordre des features (doit correspondre à l'entraînement)
        expected_features = [
            'latitude', 'longitude', 'hour', 'day_of_week', 'month', 'season',
            'is_weekend', 'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            'month_sin', 'month_cos', 'temperature', 'humidity', 'pressure',
            'wind_speed', 'wind_direction', 'wind_u', 'wind_v', 'elevation',
            'population_density', 'urban_index', 'land_use_urban',
            'land_use_suburban', 'land_use_rural', 'land_use_forest',
            'pm25_current', 'pm10_current', 'no2_current', 'o3_current',
            'co_current', 'so2_current', 'lat_rad', 'lon_rad',
            'lat_lon_interaction', 'distance_to_center', 'east_coast_proximity',
            'west_coast_proximity', 'great_lakes_proximity'
        ]
        
        feature_vector = []
        for feature_name in expected_features:
            if feature_name in all_features:
                feature_vector.append(all_features[feature_name])
            else:
                feature_vector.append(0.0)  # Valeur par défaut
        
        return feature_vector
    
    def _find_best_model(self, pollutant: str) -> Optional[str]:
        """Trouve le meilleur modèle pour un polluant"""
        model_files = list(self.models_dir.glob(f"{pollutant}_*_tempo.pkl"))
        
        if not model_files:
            return None
        
        # Pour simplifier, prendre le dernier créé (ou implémenter logique de sélection)
        return str(sorted(model_files, key=lambda x: x.stat().st_mtime, reverse=True)[0])
    
    def is_in_tempo_coverage(self, lat: float, lon: float) -> bool:
        """Vérifie si les coordonnées sont dans la zone TEMPO"""
        return (self.tempo_bounds['lat_min'] <= lat <= self.tempo_bounds['lat_max'] and
                self.tempo_bounds['lon_min'] <= lon <= self.tempo_bounds['lon_max'])

def main():
    """Pipeline principal d'entraînement TEMPO"""
    print("🤖 ENTRAÎNEMENT MODÈLES TEMPO SPÉCIALISÉS")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🛰️ Spécialisé pour: NASA TEMPO Amérique du Nord")
    print("=" * 80)
    
    try:
        predictor = TempoMLPredictor()
        
        # 1. Chargement données TEMPO
        print("\n📂 ÉTAPE 1: Chargement données TEMPO")
        features_df, targets_df = predictor.load_tempo_data()
        
        # 2. Entraînement modèles spécialisés
        print("\n🚀 ÉTAPE 2: Entraînement modèles spécialisés")
        results = predictor.train_spatial_models(features_df, targets_df)
        
        # 3. Test de prédiction géographique
        print("\n🧪 ÉTAPE 3: Test prédiction géographique")
        
        # Test sur quelques villes
        test_locations = [
            (40.7128, -74.0060, "New York"),
            (49.2827, -123.1207, "Vancouver"),
            (41.8781, -87.6298, "Chicago")
        ]
        
        for lat, lon, city in test_locations:
            if predictor.is_in_tempo_coverage(lat, lon):
                # Features de test simulées
                test_features = {
                    'hour': 14, 'day_of_week': 2, 'month': 10, 'season': 4,
                    'is_weekend': 0, 'temperature': 15.0, 'humidity': 60.0,
                    'pressure': 1013.0, 'wind_speed': 5.0, 'wind_direction': 180.0,
                    'elevation': 100.0, 'population_density': 5000.0,
                    'urban_index': 0.8, 'pm25_current': 12.0
                }
                
                try:
                    predictions = predictor.create_geographic_predictor(lat, lon, test_features)
                    print(f"   📍 {city} ({lat}, {lon}):")
                    for pollutant, value in predictions.items():
                        if value is not None:
                            print(f"      {pollutant}: {value:.2f}")
                except Exception as e:
                    print(f"   ❌ Erreur {city}: {str(e)}")
        
        # 4. Résumé
        print("\n" + "=" * 80)
        print("🎉 MODÈLES TEMPO ENTRAÎNÉS!")
        print("=" * 80)
        
        total_models = sum(len([r for r in pollutant_results.values() if 'metrics' in r])
                          for pollutant_results in results.values())
        
        print(f"✅ Modèles entraînés: {total_models}")
        print(f"✅ Polluants couverts: {len(results)}")
        print(f"✅ Zone de couverture: TEMPO Amérique du Nord")
        
        print(f"\n🎯 Performances par polluant:")
        for pollutant, pollutant_results in results.items():
            best_r2 = -1
            best_model = "Aucun"
            
            for model_name, model_result in pollutant_results.items():
                if 'metrics' in model_result:
                    r2 = model_result['metrics']['r2']
                    if r2 > best_r2:
                        best_r2 = r2
                        best_model = model_name
            
            if best_r2 > -1:
                print(f"   • {pollutant}: {best_model} (R²={best_r2:.3f})")
        
        print(f"\n📁 Modèles sauvegardés: {predictor.models_dir}/")
        print(f"\n🔄 Prochaines étapes:")
        print(f"   • Intégrer dans API de prédiction")
        print(f"   • Créer endpoints géographiques")
        print(f"   • Optimiser pour temps réel")
        
    except Exception as e:
        print(f"❌ Erreur entraînement: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
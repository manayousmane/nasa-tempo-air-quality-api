#!/usr/bin/env python3
"""
🤖 ENTRAÎNEMENT DES MODÈLES ML
================================================================================
Entraîne les modèles de prédiction de qualité de l'air
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

# Imports ML
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.impute import SimpleImputer

# Modèles avancés
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️ XGBoost non disponible - installation: pip install xgboost")

try:
    from sklearn.neural_network import MLPRegressor
    NEURAL_AVAILABLE = True
except ImportError:
    NEURAL_AVAILABLE = False

from app.core.logging import get_logger

logger = get_logger(__name__)

class AirQualityMLTrainer:
    """Entraînement des modèles de prédiction air quality"""
    
    def __init__(self, output_dir: str = "models/trained"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.imputers = {}
        self.metrics = {}
        
        # Configuration des modèles
        self.model_configs = {
            'random_forest': {
                'class': RandomForestRegressor,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 10,
                    'random_state': 42,
                    'n_jobs': -1
                }
            },
            'gradient_boosting': {
                'class': GradientBoostingRegressor,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'random_state': 42
                }
            }
        }
        
        # Ajout XGBoost si disponible
        if XGBOOST_AVAILABLE:
            self.model_configs['xgboost'] = {
                'class': xgb.XGBRegressor,
                'params': {
                    'n_estimators': 100,
                    'max_depth': 6,
                    'learning_rate': 0.1,
                    'random_state': 42
                }
            }
        
        # Ajout Neural Network si disponible
        if NEURAL_AVAILABLE:
            self.model_configs['neural_network'] = {
                'class': MLPRegressor,
                'params': {
                    'hidden_layer_sizes': (100, 50),
                    'max_iter': 500,
                    'random_state': 42
                }
            }
    
    def load_data(self, features_file: str, targets_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Charge les données processées"""
        logger.info(f"📂 Chargement données: {features_file}, {targets_file}")
        
        features_df = pd.read_csv(features_file)
        targets_df = pd.read_csv(targets_file)
        
        # Conversion timestamp si présent
        if 'timestamp' in features_df.columns:
            features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
        
        logger.info(f"✅ Features: {features_df.shape}, Targets: {targets_df.shape}")
        return features_df, targets_df
    
    def preprocess_data(self, features_df: pd.DataFrame, targets_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
        """Préprocessing des données"""
        logger.info("🔧 Préprocessing des données")
        
        # Nettoyage des données initiales
        logger.info(f"📊 Shape initiale: features{features_df.shape}, targets{targets_df.shape}")
        
        # Pour les features: exclure timestamp et colonnes avec que des NaN
        feature_columns = []
        for col in features_df.columns:
            if col != 'timestamp' and features_df[col].dtype in ['int64', 'float64']:
                # Garder seulement les colonnes qui ont des valeurs non-NaN
                if not features_df[col].isna().all():
                    feature_columns.append(col)
        
        X = features_df[feature_columns].copy()
        
        # Pour les targets: exclure colonnes avec que des NaN
        target_columns = []
        for col in targets_df.columns:
            if not targets_df[col].isna().all():
                target_columns.append(col)
        
        y = targets_df[target_columns].copy()
        
        logger.info(f"📊 Colonnes conservées: features={len(feature_columns)}, targets={len(target_columns)}")
        logger.info(f"📊 Features: {feature_columns[:10]}...")  # Premiers 10
        logger.info(f"📊 Targets: {target_columns}")
        
        # Gestion des valeurs manquantes - Features
        self.imputers['features'] = SimpleImputer(strategy='median')
        X_imputed = self.imputers['features'].fit_transform(X)
        X = pd.DataFrame(X_imputed, columns=feature_columns)
        
        # Gestion des valeurs manquantes - Targets
        self.imputers['targets'] = SimpleImputer(strategy='median')
        y_imputed = self.imputers['targets'].fit_transform(y)
        y = pd.DataFrame(y_imputed, columns=target_columns)
        
        # Normalisation des features
        self.scalers['features'] = StandardScaler()
        X_scaled = self.scalers['features'].fit_transform(X)
        
        logger.info(f"✅ Préprocessing terminé: X{X_scaled.shape}, y{y.shape}")
        return X_scaled, y.values, feature_columns, target_columns
    
    def train_models(self, X: np.ndarray, y: np.ndarray, 
                     feature_columns: List[str], target_columns: List[str]) -> Dict:
        """Entraîne tous les modèles"""
        logger.info("🚀 Début entraînement des modèles")
        
        results = {}
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Entraînement pour chaque target (polluant)
        for target_idx, target_name in enumerate(target_columns):
            logger.info(f"🎯 Entraînement pour: {target_name}")
            
            y_train_target = y_train[:, target_idx]
            y_test_target = y_test[:, target_idx]
            
            target_results = {}
            
            # Entraînement de chaque modèle
            for model_name, config in self.model_configs.items():
                try:
                    logger.info(f"   🔄 Modèle: {model_name}")
                    
                    # Création et entraînement du modèle
                    model = config['class'](**config['params'])
                    model.fit(X_train, y_train_target)
                    
                    # Prédictions
                    y_pred_train = model.predict(X_train)
                    y_pred_test = model.predict(X_test)
                    
                    # Métriques
                    metrics = {
                        'train_rmse': np.sqrt(mean_squared_error(y_train_target, y_pred_train)),
                        'test_rmse': np.sqrt(mean_squared_error(y_test_target, y_pred_test)),
                        'train_mae': mean_absolute_error(y_train_target, y_pred_train),
                        'test_mae': mean_absolute_error(y_test_target, y_pred_test),
                        'train_r2': r2_score(y_train_target, y_pred_train),
                        'test_r2': r2_score(y_test_target, y_pred_test)
                    }
                    
                    # Sauvegarde du modèle
                    model_file = self.output_dir / f"{target_name}_{model_name}_model.pkl"
                    with open(model_file, 'wb') as f:
                        pickle.dump(model, f)
                    
                    target_results[model_name] = {
                        'model_file': str(model_file),
                        'metrics': metrics
                    }
                    
                    logger.info(f"   ✅ {model_name}: R²={metrics['test_r2']:.3f}, RMSE={metrics['test_rmse']:.3f}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Erreur {model_name}: {str(e)}")
                    target_results[model_name] = {'error': str(e)}
            
            results[target_name] = target_results
        
        # Sauvegarde des preprocessors
        preprocessors_file = self.output_dir / "preprocessors.pkl"
        with open(preprocessors_file, 'wb') as f:
            pickle.dump({
                'scalers': self.scalers,
                'imputers': self.imputers,
                'feature_columns': feature_columns,
                'target_columns': target_columns
            }, f)
        
        logger.info(f"✅ Preprocessors sauvegardés: {preprocessors_file}")
        
        return results
    
    def save_training_report(self, results: Dict, features_df: pd.DataFrame, targets_df: pd.DataFrame):
        """Sauvegarde le rapport d'entraînement"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            'timestamp': timestamp,
            'data_info': {
                'features_shape': features_df.shape,
                'targets_shape': targets_df.shape,
                'features_columns': list(features_df.columns),
                'targets_columns': list(targets_df.columns)
            },
            'models_trained': list(self.model_configs.keys()),
            'results': results,
            'summary': self._create_summary(results)
        }
        
        report_file = self.output_dir / f"training_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Rapport sauvegardé: {report_file}")
        return report_file
    
    def _create_summary(self, results: Dict) -> Dict:
        """Crée un résumé des performances"""
        summary = {
            'best_models': {},
            'average_performance': {},
            'total_models_trained': 0
        }
        
        for target_name, target_results in results.items():
            best_r2 = -float('inf')
            best_model = None
            
            valid_results = []
            
            for model_name, model_result in target_results.items():
                if 'metrics' in model_result:
                    summary['total_models_trained'] += 1
                    metrics = model_result['metrics']
                    
                    if metrics['test_r2'] > best_r2:
                        best_r2 = metrics['test_r2']
                        best_model = model_name
                    
                    valid_results.append(metrics)
            
            if best_model:
                summary['best_models'][target_name] = {
                    'model': best_model,
                    'r2_score': best_r2
                }
            
            if valid_results:
                avg_metrics = {}
                for metric in ['test_r2', 'test_rmse', 'test_mae']:
                    values = [r[metric] for r in valid_results]
                    avg_metrics[metric] = np.mean(values)
                
                summary['average_performance'][target_name] = avg_metrics
        
        return summary

def find_latest_data_files(data_dir: str = "data/processed") -> Tuple[Optional[str], Optional[str]]:
    """Trouve les fichiers de données les plus récents"""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return None, None
    
    features_files = list(data_path.glob("features_*.csv"))
    targets_files = list(data_path.glob("targets_*.csv"))
    
    if not features_files or not targets_files:
        return None, None
    
    # Tri par date de modification
    features_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    targets_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return str(features_files[0]), str(targets_files[0])

def main():
    """Pipeline principal d'entraînement"""
    print("🤖 ENTRAÎNEMENT DES MODÈLES ML")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 1. Recherche des données
        print("\n🔍 ÉTAPE 1: Recherche des données")
        features_file, targets_file = find_latest_data_files()
        
        if not features_file or not targets_file:
            print("❌ Aucun fichier de données trouvé")
            print("💡 Exécutez d'abord: python data_pipeline_ml.py")
            return
        
        print(f"✅ Features: {features_file}")
        print(f"✅ Targets: {targets_file}")
        
        # 2. Initialisation du trainer
        trainer = AirQualityMLTrainer()
        
        # 3. Chargement des données
        print("\n📂 ÉTAPE 2: Chargement des données")
        features_df, targets_df = trainer.load_data(features_file, targets_file)
        
        # 4. Préprocessing
        print("\n🔧 ÉTAPE 3: Préprocessing")
        X, y, feature_columns, target_columns = trainer.preprocess_data(features_df, targets_df)
        
        # 5. Entraînement
        print("\n🚀 ÉTAPE 4: Entraînement des modèles")
        results = trainer.train_models(X, y, feature_columns, target_columns)
        
        # 6. Sauvegarde du rapport
        print("\n📊 ÉTAPE 5: Génération du rapport")
        report_file = trainer.save_training_report(results, features_df, targets_df)
        
        # 7. Résumé
        print("\n" + "=" * 80)
        print("🎉 ENTRAÎNEMENT TERMINÉ!")
        print("=" * 80)
        
        total_models = sum(len([r for r in target_results.values() if 'metrics' in r]) 
                          for target_results in results.values())
        
        print(f"✅ Modèles entraînés: {total_models}")
        print(f"✅ Polluants couverts: {len(target_columns)}")
        print(f"✅ Algorithmes utilisés: {len(trainer.model_configs)}")
        
        print(f"\n🎯 Meilleurs modèles par polluant:")
        for target_name, target_results in results.items():
            best_r2 = -1
            best_model = "Aucun"
            
            for model_name, model_result in target_results.items():
                if 'metrics' in model_result:
                    r2 = model_result['metrics']['test_r2']
                    if r2 > best_r2:
                        best_r2 = r2
                        best_model = model_name
            
            if best_r2 > -1:
                print(f"   • {target_name}: {best_model} (R²={best_r2:.3f})")
        
        print(f"\n📁 Fichiers générés:")
        print(f"   • Modèles: {trainer.output_dir}/")
        print(f"   • Rapport: {report_file}")
        
        print(f"\n🔄 Prochaines étapes:")
        print(f"   • Tester les modèles en prédiction")
        print(f"   • Intégrer dans l'API de prédiction")
        print(f"   • Optimiser les hyperparamètres")
        
    except Exception as e:
        print(f"❌ Erreur entraînement: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
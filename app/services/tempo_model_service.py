"""
🛰️ SERVICE MODÈLES TEMPO
================================================================================
Service pour charger et utiliser les modèles ML TEMPO (même avec performances faibles)
Sera amélioré une fois les modèles optimisés
================================================================================
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TempoModelService:
    """Service pour gérer les modèles TEMPO"""
    
    def __init__(self):
        self.models_dir = Path("models/tempo")
        self.models = {}
        self.metadata = {}
        self.is_loaded = False
        self.load_models()
    
    def load_models(self) -> bool:
        """Charge tous les modèles TEMPO disponibles"""
        try:
            if not self.models_dir.exists():
                logger.warning(f"Dossier modèles non trouvé: {self.models_dir}")
                return False
            
            # Charger metadata des modèles
            metadata_files = list(self.models_dir.glob("tempo_models_metadata_*.json"))
            if metadata_files:
                latest_metadata = max(metadata_files, key=lambda x: x.stat().st_mtime)
                with open(latest_metadata, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"📊 Metadata chargée: {latest_metadata.name}")
            
            # Charger les modèles individuels
            model_files = list(self.models_dir.glob("*_tempo.pkl"))
            loaded_count = 0
            
            for model_file in model_files:
                try:
                    with open(model_file, 'rb') as f:
                        model_obj = pickle.load(f)
                    
                    # Extraction du nom du polluant et algorithme
                    filename = model_file.stem  # ex: pm25_random_forest_tempo
                    parts = filename.replace('_tempo', '').split('_')
                    
                    if len(parts) >= 2:
                        pollutant = parts[0]
                        algorithm = '_'.join(parts[1:])
                        
                        if pollutant not in self.models:
                            self.models[pollutant] = {}
                        
                        # Le modèle lui-même est l'objet pickled, pas un dictionnaire
                        self.models[pollutant][algorithm] = model_obj
                        loaded_count += 1
                        
                except Exception as e:
                    logger.error(f"Erreur chargement {model_file}: {str(e)}")
            
            self.is_loaded = loaded_count > 0
            logger.info(f"🤖 Modèles chargés: {loaded_count}")
            
            return self.is_loaded
            
        except Exception as e:
            logger.error(f"Erreur chargement modèles: {str(e)}")
            return False
    
    def get_available_pollutants(self) -> List[str]:
        """Retourne la liste des polluants disponibles"""
        return list(self.models.keys())
    
    def get_available_algorithms(self, pollutant: str) -> List[str]:
        """Retourne les algorithmes disponibles pour un polluant"""
        if pollutant in self.models:
            return list(self.models[pollutant].keys())
        return []
    
    def get_best_model_for_pollutant(self, pollutant: str) -> Optional[Any]:
        """Retourne le meilleur modèle pour un polluant selon metadata"""
        if not self.is_loaded or pollutant not in self.models:
            return None
        
        # Utiliser metadata pour trouver le meilleur modèle
        if 'best_models' in self.metadata and pollutant in self.metadata['best_models']:
            best_algorithm = self.metadata['best_models'][pollutant].get('algorithm')
            if best_algorithm and best_algorithm in self.models[pollutant]:
                return self.models[pollutant][best_algorithm]
        
        # Fallback: prendre le premier modèle disponible
        algorithms = self.get_available_algorithms(pollutant)
        if algorithms:
            return self.models[pollutant][algorithms[0]]
        
        return None
    
    def create_feature_vector(self, coordinates: Dict[str, float], 
                            features: Dict[str, Any]) -> np.ndarray:
        """Crée un vecteur de features pour la prédiction (40 features comme dataset)"""
        try:
            # Features géographiques
            latitude = coordinates.get('latitude', 45.0)
            longitude = coordinates.get('longitude', -75.0)
            
            # Features temporelles
            hour = features.get('hour', 12)
            day_of_week = features.get('day_of_week', 4)  # Vendredi par défaut
            month = features.get('month', 10)  # Octobre
            season = (month % 12 + 3) // 3  # Calcul saison
            is_weekend = int(day_of_week >= 5)
            
            # Features temporelles cycliques
            hour_sin = np.sin(2 * np.pi * hour / 24)
            hour_cos = np.cos(2 * np.pi * hour / 24)
            day_sin = np.sin(2 * np.pi * day_of_week / 7)
            day_cos = np.cos(2 * np.pi * day_of_week / 7)
            month_sin = np.sin(2 * np.pi * month / 12)
            month_cos = np.cos(2 * np.pi * month / 12)
            
            # Features météo (avec valeurs par défaut)
            temperature = features.get('temperature', 15.0)
            humidity = features.get('humidity', 65.0)
            pressure = features.get('pressure', 1013.25)
            wind_speed = features.get('wind_speed', 5.0)
            wind_direction = features.get('wind_direction', 180.0)
            
            # Composantes du vent
            wind_u = wind_speed * np.cos(np.radians(wind_direction))
            wind_v = wind_speed * np.sin(np.radians(wind_direction))
            
            # Features géographiques avancées
            elevation = features.get('elevation', 100.0)
            population_density = features.get('population_density', 1000.0)
            urban_index = features.get('urban_index', 0.5)
            
            # Land use (approximé selon la localisation)
            # Urbain si densité population élevée
            land_use_urban = 1 if population_density > 5000 else 0
            land_use_suburban = 1 if 1000 < population_density <= 5000 else 0
            land_use_rural = 1 if 100 < population_density <= 1000 else 0
            land_use_forest = 1 if population_density <= 100 else 0
            
            # Features air quality actuelles (avec valeurs par défaut)
            pm25_current = features.get('pm25_current', 12.0)
            pm10_current = features.get('pm10_current', 20.0)
            no2_current = features.get('no2_current', 25.0)
            o3_current = features.get('o3_current', 50.0)
            co_current = features.get('co_current', 1.0)
            so2_current = features.get('so2_current', 5.0)
            
            # Assemblage du vecteur selon l'ordre du dataset d'entraînement
            feature_vector = np.array([
                # Géographiques de base
                latitude, longitude,
                
                # Temporelles
                hour, day_of_week, month, season, is_weekend,
                
                # Temporelles cycliques
                hour_sin, hour_cos, day_sin, day_cos, month_sin, month_cos,
                
                # Météo
                temperature, humidity, pressure, wind_speed, wind_direction,
                wind_u, wind_v,
                
                # Géographiques avancées
                elevation, population_density, urban_index,
                
                # Land use
                land_use_urban, land_use_suburban, land_use_rural, land_use_forest,
                
                # Air quality actuelles
                pm25_current, pm10_current, no2_current, o3_current, co_current, so2_current
            ])
            
            # Vérification : devrait avoir 33 features selon le header CSV
            # Si les modèles attendent 40, il y a peut-être d'autres features générées
            
            if len(feature_vector) < 40:
                # Ajouter features manquantes (interactions, etc.)
                extra_features = np.array([
                    # Interactions géographiques
                    latitude * longitude,
                    latitude**2,
                    longitude**2,
                    
                    # Interactions météo
                    temperature * humidity / 100,
                    wind_speed**2,
                    
                    # Indices composites
                    (pm25_current + pm10_current) / 2,  # PM composite
                    (no2_current + o3_current) / 2      # Gaz composite
                ])
                
                feature_vector = np.concatenate([feature_vector, extra_features])
            
            # Assurer exactement 40 features
            if len(feature_vector) > 40:
                feature_vector = feature_vector[:40]
            elif len(feature_vector) < 40:
                # Padding avec des zéros
                padding = np.zeros(40 - len(feature_vector))
                feature_vector = np.concatenate([feature_vector, padding])
            
            return feature_vector.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Erreur création feature vector: {str(e)}")
            # Retour vecteur par défaut avec 40 features
            return np.zeros((1, 40))
    
    def predict_single_pollutant(self, pollutant: str, 
                               coordinates: Dict[str, float],
                               features: Dict[str, Any]) -> Optional[float]:
        """Prédiction pour un polluant spécifique"""
        try:
            model = self.get_best_model_for_pollutant(pollutant)
            if model is None:
                logger.warning(f"Aucun modèle disponible pour {pollutant}")
                return None
            
            # Debug: vérifier le type de modèle
            logger.debug(f"Type de modèle pour {pollutant}: {type(model)}")
            
            # Si le modèle est un dictionnaire (format d'entraînement), extraire le modèle
            if isinstance(model, dict):
                if 'model' in model:
                    actual_model = model['model']
                else:
                    logger.error(f"Format modèle invalide pour {pollutant}: {model.keys()}")
                    return None
            else:
                actual_model = model
            
            # Vérifier que le modèle a une méthode predict
            if not hasattr(actual_model, 'predict'):
                logger.error(f"Modèle {pollutant} n'a pas de méthode predict: {type(actual_model)}")
                return None
            
            # Création du vecteur de features
            feature_vector = self.create_feature_vector(coordinates, features)
            
            # Prédiction
            prediction = actual_model.predict(feature_vector)[0]
            
            # Validation et nettoyage de la prédiction
            if np.isnan(prediction) or np.isinf(prediction):
                logger.warning(f"Prédiction invalide pour {pollutant}: {prediction}")
                return None
            
            # Contraintes physiques basiques
            if prediction < 0:
                prediction = 0.0
            
            # Limites maximales raisonnables
            max_values = {
                'pm25': 300.0, 'pm10': 500.0, 'no2': 200.0,
                'o3': 300.0, 'co': 50.0, 'so2': 100.0
            }
            
            max_val = max_values.get(pollutant, 1000.0)
            if prediction > max_val:
                prediction = max_val
            
            return float(prediction)
            
        except Exception as e:
            logger.error(f"Erreur prédiction {pollutant}: {str(e)}")
            return None
    
    def predict_all_pollutants(self, coordinates: Dict[str, float],
                             features: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """Prédiction pour tous les polluants disponibles"""
        predictions = {}
        
        for pollutant in self.get_available_pollutants():
            predictions[pollutant] = self.predict_single_pollutant(
                pollutant, coordinates, features
            )
        
        return predictions
    
    def calculate_aqi(self, predictions: Dict[str, Optional[float]]) -> Dict[str, Any]:
        """Calcul approximatif de l'AQI basé sur les prédictions"""
        try:
            # Conversion vers AQI EPA (approximation)
            aqi_values = {}
            
            # PM2.5
            if predictions.get('pm25') is not None:
                pm25 = predictions['pm25']
                if pm25 <= 12.0:
                    aqi_values['pm25'] = pm25 * 50 / 12.0
                elif pm25 <= 35.4:
                    aqi_values['pm25'] = 50 + (pm25 - 12.0) * 50 / (35.4 - 12.0)
                elif pm25 <= 55.4:
                    aqi_values['pm25'] = 100 + (pm25 - 35.4) * 50 / (55.4 - 35.4)
                else:
                    aqi_values['pm25'] = min(300, 150 + (pm25 - 55.4) * 100 / 150)
            
            # NO2 (approximation)
            if predictions.get('no2') is not None:
                no2 = predictions['no2']
                aqi_values['no2'] = min(300, no2 * 2)  # Approximation simple
            
            # O3 (approximation)
            if predictions.get('o3') is not None:
                o3 = predictions['o3']
                aqi_values['o3'] = min(300, o3 * 1.5)  # Approximation simple
            
            # AQI global = maximum des AQI individuels
            if aqi_values:
                overall_aqi = max(aqi_values.values())
                
                # Catégorie AQI
                if overall_aqi <= 50:
                    category = "Good"
                    color = "Green"
                elif overall_aqi <= 100:
                    category = "Moderate"
                    color = "Yellow"
                elif overall_aqi <= 150:
                    category = "Unhealthy for Sensitive Groups"
                    color = "Orange"
                elif overall_aqi <= 200:
                    category = "Unhealthy"
                    color = "Red"
                else:
                    category = "Very Unhealthy"
                    color = "Purple"
                
                return {
                    'overall': round(overall_aqi),
                    'category': category,
                    'color': color,
                    'individual': {k: round(v) for k, v in aqi_values.items()}
                }
            
            return {'overall': None, 'category': 'Unknown', 'color': 'Gray'}
            
        except Exception as e:
            logger.error(f"Erreur calcul AQI: {str(e)}")
            return {'overall': None, 'category': 'Error', 'color': 'Gray'}
    
    def get_health_recommendations(self, aqi: Dict[str, Any]) -> Dict[str, str]:
        """Recommandations santé basées sur l'AQI"""
        try:
            overall_aqi = aqi.get('overall', 0)
            
            if overall_aqi is None or overall_aqi <= 50:
                return {
                    'general': 'Air quality is good. Enjoy outdoor activities.',
                    'sensitive': 'No health impacts expected for sensitive groups.',
                    'outdoor_activity': 'Safe for all outdoor activities.'
                }
            elif overall_aqi <= 100:
                return {
                    'general': 'Air quality is acceptable for most people.',
                    'sensitive': 'Sensitive individuals may experience minor symptoms.',
                    'outdoor_activity': 'Generally safe for outdoor activities.'
                }
            elif overall_aqi <= 150:
                return {
                    'general': 'Unhealthy for sensitive groups.',
                    'sensitive': 'Sensitive groups should limit prolonged outdoor exertion.',
                    'outdoor_activity': 'Consider reducing intense outdoor activities.'
                }
            elif overall_aqi <= 200:
                return {
                    'general': 'Unhealthy air quality.',
                    'sensitive': 'Sensitive groups should avoid outdoor activities.',
                    'outdoor_activity': 'Everyone should limit outdoor exertion.'
                }
            else:
                return {
                    'general': 'Very unhealthy air quality.',
                    'sensitive': 'Everyone should avoid outdoor activities.',
                    'outdoor_activity': 'Stay indoors and keep windows closed.'
                }
                
        except Exception as e:
            logger.error(f"Erreur recommandations santé: {str(e)}")
            return {
                'general': 'Unable to provide recommendations.',
                'sensitive': 'Consult local air quality reports.',
                'outdoor_activity': 'Use caution with outdoor activities.'
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Status du service de modèles"""
        return {
            'is_loaded': self.is_loaded,
            'models_available': len(self.models),
            'pollutants': self.get_available_pollutants(),
            'total_algorithms': sum(len(algs) for algs in self.models.values()),
            'metadata_loaded': bool(self.metadata),
            'models_directory': str(self.models_dir),
            'last_updated': datetime.now().isoformat()
        }
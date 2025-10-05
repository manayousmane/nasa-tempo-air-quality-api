"""
Machine learning service for air quality predictions.
"""
import pickle
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import AirQualityPrediction

logger = get_logger(__name__)


class MLService:
    """Service for machine learning operations."""
    
    def __init__(self):
        self.model_path = Path(settings.MODEL_DATA_PATH)
        self.models = {}
        self.model_metadata = {}
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained ML models."""
        try:
            if not self.model_path.exists():
                logger.warning(f"Model path {self.model_path} does not exist")
                return
            
            # Load different models for different pollutants
            model_files = {
                "pm25": "pm25_xgboost_model.pkl",
                "no2": "no2_lstm_model.pkl", 
                "o3": "o3_ensemble_model.pkl",
                "aqi": "aqi_combined_model.pkl"
            }
            
            for pollutant, filename in model_files.items():
                model_file = self.model_path / filename
                if model_file.exists():
                    try:
                        self.models[pollutant] = joblib.load(model_file)
                        logger.info(f"Loaded model for {pollutant}")
                        
                        # Load metadata if available
                        metadata_file = self.model_path / f"{pollutant}_metadata.json"
                        if metadata_file.exists():
                            import json
                            with open(metadata_file) as f:
                                self.model_metadata[pollutant] = json.load(f)
                                
                    except Exception as e:
                        logger.error(f"Error loading model for {pollutant}: {e}")
                else:
                    logger.warning(f"Model file not found: {model_file}")
                    
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    async def generate_forecast(self,
                              latitude: float,
                              longitude: float,
                              hours: int = 24,
                              historical_data: List[Dict[str, Any]] = None,
                              model_version: Optional[str] = None) -> List[AirQualityPrediction]:
        """
        Generate air quality forecast using ML models.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            hours: Forecast horizon in hours
            historical_data: Historical data for context
            model_version: Optional specific model version
        
        Returns:
            List of air quality predictions
        """
        try:
            if not self.models:
                logger.warning("No models loaded, returning empty forecast")
                return []
            
            # Prepare input features
            features = await self._prepare_features(
                latitude, longitude, historical_data
            )
            
            if features is None:
                logger.warning("Could not prepare features for prediction")
                return []
            
            # Generate predictions for each hour
            predictions = []
            current_time = datetime.utcnow()
            
            for hour in range(1, hours + 1):
                forecast_time = current_time + timedelta(hours=hour)
                
                # Create prediction for this time step
                prediction = await self._predict_single_timestep(
                    features, hour, forecast_time, model_version
                )
                
                if prediction:
                    predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return []
    
    async def _prepare_features(self,
                              latitude: float,
                              longitude: float,
                              historical_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Prepare input features for ML models.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            historical_data: Historical measurements
        
        Returns:
            Feature dictionary for models
        """
        try:
            features = {
                # Location features
                "latitude": latitude,
                "longitude": longitude,
                
                # Time features
                "hour": datetime.utcnow().hour,
                "day_of_week": datetime.utcnow().weekday(),
                "month": datetime.utcnow().month,
                "is_weekend": datetime.utcnow().weekday() >= 5,
                
                # Seasonal features
                "season": self._get_season(datetime.utcnow()),
                
                # Historical pollutant levels (last 24 hours)
                "pm25_24h_avg": 0.0,
                "no2_24h_avg": 0.0,
                "o3_24h_avg": 0.0,
                "pm25_trend": 0.0,  # Increasing/decreasing trend
                
                # Weather features (would be populated from weather data)
                "temperature": 20.0,  # Default values
                "humidity": 50.0,
                "wind_speed": 5.0,
                "wind_direction": 180.0,
                "pressure": 1013.25,
                "precipitation": 0.0,
                
                # Air quality indices
                "aqi_24h_avg": 50.0,
                "aqi_trend": 0.0
            }
            
            # Process historical data if available
            if historical_data:
                features.update(self._extract_historical_features(historical_data))
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return None
    
    async def _predict_single_timestep(self,
                                     features: Dict[str, Any],
                                     hour_ahead: int,
                                     forecast_time: datetime,
                                     model_version: Optional[str] = None) -> Optional[AirQualityPrediction]:
        """
        Generate prediction for a single time step.
        
        Args:
            features: Input features
            hour_ahead: How many hours ahead
            forecast_time: Target prediction time
            model_version: Optional model version
        
        Returns:
            Air quality prediction
        """
        try:
            # Adjust features for time horizon
            adjusted_features = features.copy()
            adjusted_features["hour"] = forecast_time.hour
            adjusted_features["forecast_horizon"] = hour_ahead
            
            # Convert to numpy array for model input
            feature_array = self._features_to_array(adjusted_features)
            
            # Generate predictions for each pollutant
            predictions = {}
            confidence_scores = {}
            
            for pollutant, model in self.models.items():
                try:
                    if pollutant == "aqi":
                        continue  # Calculate AQI from individual pollutants
                    
                    # Make prediction
                    pred_value = model.predict(feature_array.reshape(1, -1))[0]
                    predictions[f"predicted_{pollutant}"] = max(0, float(pred_value))
                    
                    # Calculate confidence (simplified)
                    confidence_scores[pollutant] = self._calculate_prediction_confidence(
                        model, feature_array, hour_ahead
                    )
                    
                except Exception as e:
                    logger.error(f"Error predicting {pollutant}: {e}")
                    continue
            
            # Calculate AQI from individual pollutant predictions
            if "predicted_pm25" in predictions or "predicted_no2" in predictions:
                predicted_aqi = self._calculate_aqi_from_pollutants(predictions)
                predictions["predicted_aqi"] = predicted_aqi
                predictions["predicted_category"] = self._get_aqi_category(predicted_aqi)
            
            # Calculate confidence intervals (simplified)
            confidence_intervals = self._calculate_confidence_intervals(predictions, confidence_scores)
            
            # Create prediction object
            prediction = AirQualityPrediction(
                id=0,
                location_id=0,
                model_version=model_version or "default_v1.0",
                prediction_timestamp=datetime.utcnow(),
                forecast_timestamp=forecast_time,
                forecast_horizon=hour_ahead,
                model_confidence=sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.7,
                created_at=datetime.utcnow(),
                **predictions,
                **confidence_intervals
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting single timestep: {e}")
            return None
    
    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dictionary to numpy array for model input."""
        try:
            # Define expected feature order (would be saved with model)
            feature_order = [
                "latitude", "longitude", "hour", "day_of_week", "month", "is_weekend",
                "season", "temperature", "humidity", "wind_speed", "wind_direction",
                "pressure", "precipitation", "pm25_24h_avg", "no2_24h_avg", "o3_24h_avg",
                "pm25_trend", "aqi_24h_avg", "aqi_trend", "forecast_horizon"
            ]
            
            # Convert boolean to int
            feature_array = []
            for feature_name in feature_order:
                value = features.get(feature_name, 0.0)
                if isinstance(value, bool):
                    value = float(value)
                feature_array.append(float(value))
            
            return np.array(feature_array)
            
        except Exception as e:
            logger.error(f"Error converting features to array: {e}")
            return np.zeros(20)  # Default array
    
    def _extract_historical_features(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract features from historical data."""
        try:
            features = {}
            
            if not historical_data:
                return features
            
            # Sort by timestamp
            sorted_data = sorted(historical_data, key=lambda x: x.get('timestamp', datetime.min))
            
            # Calculate 24-hour averages for pollutants
            pollutants = ["pm25", "no2", "o3"]
            for pollutant in pollutants:
                values = [d.get(pollutant) for d in sorted_data if d.get(pollutant) is not None]
                if values:
                    features[f"{pollutant}_24h_avg"] = sum(values) / len(values)
                    
                    # Calculate trend (simple linear trend)
                    if len(values) > 1:
                        x = np.arange(len(values))
                        y = np.array(values)
                        trend = np.polyfit(x, y, 1)[0]  # Slope of linear fit
                        features[f"{pollutant}_trend"] = trend
            
            # Calculate AQI features
            aqi_values = [d.get("aqi") for d in sorted_data if d.get("aqi") is not None]
            if aqi_values:
                features["aqi_24h_avg"] = sum(aqi_values) / len(aqi_values)
                if len(aqi_values) > 1:
                    x = np.arange(len(aqi_values))
                    y = np.array(aqi_values)
                    features["aqi_trend"] = np.polyfit(x, y, 1)[0]
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting historical features: {e}")
            return {}
    
    def _calculate_prediction_confidence(self, model, features: np.ndarray, hour_ahead: int) -> float:
        """Calculate confidence score for a prediction."""
        try:
            # Simplified confidence calculation
            # In practice, this would use model-specific methods like:
            # - Ensemble variance for random forests
            # - Dropout uncertainty for neural networks
            # - Cross-validation scores
            
            base_confidence = 0.8
            
            # Reduce confidence for longer horizons
            horizon_penalty = min(0.3, hour_ahead * 0.01)
            
            # Model-specific adjustments
            model_type = type(model).__name__.lower()
            if "xgboost" in model_type:
                model_bonus = 0.1
            elif "lstm" in model_type:
                model_bonus = 0.05
            else:
                model_bonus = 0.0
            
            confidence = base_confidence - horizon_penalty + model_bonus
            return max(0.1, min(0.95, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return 0.7
    
    def _calculate_aqi_from_pollutants(self, predictions: Dict[str, float]) -> int:
        """Calculate AQI from individual pollutant predictions."""
        try:
            aqi_values = []
            
            # PM2.5 AQI
            if "predicted_pm25" in predictions:
                pm25 = predictions["predicted_pm25"]
                if pm25 <= 12.0:
                    aqi_pm25 = (50 / 12.0) * pm25
                elif pm25 <= 35.4:
                    aqi_pm25 = 50 + ((100 - 50) / (35.4 - 12.1)) * (pm25 - 12.1)
                elif pm25 <= 55.4:
                    aqi_pm25 = 100 + ((150 - 100) / (55.4 - 35.5)) * (pm25 - 35.5)
                else:
                    aqi_pm25 = min(500, 150 + ((500 - 150) / (500 - 55.5)) * (pm25 - 55.5))
                aqi_values.append(aqi_pm25)
            
            # NO2 AQI (simplified)
            if "predicted_no2" in predictions:
                no2 = predictions["predicted_no2"]
                if no2 <= 53:
                    aqi_no2 = (50 / 53) * no2
                elif no2 <= 100:
                    aqi_no2 = 50 + ((100 - 50) / (100 - 54)) * (no2 - 54)
                else:
                    aqi_no2 = min(500, 100 + ((500 - 100) / (2000 - 101)) * (no2 - 101))
                aqi_values.append(aqi_no2)
            
            # O3 AQI (simplified)
            if "predicted_o3" in predictions:
                o3 = predictions["predicted_o3"]
                if o3 <= 54:
                    aqi_o3 = (50 / 54) * o3
                elif o3 <= 70:
                    aqi_o3 = 50 + ((100 - 50) / (70 - 55)) * (o3 - 55)
                else:
                    aqi_o3 = min(500, 100 + ((500 - 100) / (405 - 71)) * (o3 - 71))
                aqi_values.append(aqi_o3)
            
            return int(max(aqi_values)) if aqi_values else 50
            
        except Exception as e:
            logger.error(f"Error calculating AQI: {e}")
            return 50
    
    def _get_aqi_category(self, aqi: int) -> str:
        """Get AQI category from numeric value."""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def _calculate_confidence_intervals(self, predictions: Dict[str, float], confidence_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate confidence intervals for predictions."""
        try:
            intervals = {}
            
            # Simple confidence interval calculation
            # In practice, this would use model-specific uncertainty estimates
            
            if "predicted_pm25" in predictions:
                pm25 = predictions["predicted_pm25"]
                confidence = confidence_scores.get("pm25", 0.7)
                margin = pm25 * (1 - confidence) * 0.5
                intervals["pm25_confidence_low"] = max(0, pm25 - margin)
                intervals["pm25_confidence_high"] = pm25 + margin
            
            if "predicted_aqi" in predictions:
                aqi = predictions["predicted_aqi"]
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.7
                margin = aqi * (1 - avg_confidence) * 0.3
                intervals["aqi_confidence_low"] = max(0, int(aqi - margin))
                intervals["aqi_confidence_high"] = min(500, int(aqi + margin))
            
            return intervals
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {e}")
            return {}
    
    def _get_season(self, date: datetime) -> int:
        """Get season number from date (0=winter, 1=spring, 2=summer, 3=fall)."""
        month = date.month
        if month in [12, 1, 2]:
            return 0  # Winter
        elif month in [3, 4, 5]:
            return 1  # Spring
        elif month in [6, 7, 8]:
            return 2  # Summer
        else:
            return 3  # Fall
    
    async def retrain_models(self, training_data: List[Dict[str, Any]]) -> bool:
        """
        Retrain ML models with new data.
        
        Args:
            training_data: New training data
        
        Returns:
            True if retraining successful
        """
        try:
            logger.info("Starting model retraining")
            
            # This would implement the full retraining pipeline:
            # 1. Prepare training data
            # 2. Feature engineering
            # 3. Model training
            # 4. Validation
            # 5. Model saving
            
            # Placeholder implementation
            logger.info("Model retraining completed (placeholder)")
            return True
            
        except Exception as e:
            logger.error(f"Error retraining models: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            "loaded_models": list(self.models.keys()),
            "model_path": str(self.model_path),
            "metadata": self.model_metadata,
            "last_update": datetime.utcnow().isoformat()
        }
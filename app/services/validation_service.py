"""
Data validation service for air quality API.
Implements comprehensive validation, sanitization and quality checks.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataValidationService:
    """Service de validation et qualité des données"""
    
    # Plages valides pour les polluants (concentrations en µg/m³ ou ppb)
    POLLUTANT_RANGES = {
        "pm25": {"min": 0.0, "max": 1000.0, "unit": "µg/m³"},
        "pm2.5": {"min": 0.0, "max": 1000.0, "unit": "µg/m³"},  # Alias
        "pm10": {"min": 0.0, "max": 2000.0, "unit": "µg/m³"},
        "no2": {"min": 0.0, "max": 500.0, "unit": "ppb"},
        "o3": {"min": 0.0, "max": 300.0, "unit": "ppb"},
        "co": {"min": 0.0, "max": 50.0, "unit": "ppm"},
        "so2": {"min": 0.0, "max": 200.0, "unit": "ppb"},
        "hcho": {"min": 0.0, "max": 100.0, "unit": "ppb"},  # Formaldéhyde
        "nh3": {"min": 0.0, "max": 100.0, "unit": "ppb"},   # Ammoniac
    }
    
    # Seuils de qualité AQI
    AQI_RANGES = {
        "good": (0, 50),
        "moderate": (51, 100),
        "unhealthy_sensitive": (101, 150),
        "unhealthy": (151, 200),
        "very_unhealthy": (201, 300),
        "hazardous": (301, 500)
    }
    
    def __init__(self):
        logger.info("🔍 DataValidationService initialisé")
    
    def validate_coordinates(self, latitude: float, longitude: float) -> Tuple[bool, str]:
        """
        Valide les coordonnées géographiques.
        
        Args:
            latitude: Latitude à valider
            longitude: Longitude à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            # Vérification des types
            if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                return False, "Coordinates must be numeric"
            
            # Vérification des plages
            if not (-90 <= latitude <= 90):
                return False, f"Latitude {latitude} out of range [-90, 90]"
            
            if not (-180 <= longitude <= 180):
                return False, f"Longitude {longitude} out of range [-180, 180]"
            
            # Vérification de précision raisonnable (pas trop de décimales)
            if len(str(latitude).split('.')[-1]) > 6 or len(str(longitude).split('.')[-1]) > 6:
                return False, "Coordinates precision too high (max 6 decimal places)"
            
            return True, ""
            
        except Exception as e:
            return False, f"Coordinate validation error: {str(e)}"
    
    def validate_pollutant_data(self, pollutant: str, concentration: float, 
                              unit: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valide les données de polluant.
        
        Args:
            pollutant: Nom du polluant
            concentration: Concentration mesurée
            unit: Unité de mesure
            
        Returns:
            Tuple (is_valid, error_message, quality_info)
        """
        try:
            pollutant_lower = pollutant.lower()
            
            # Vérifier si le polluant est connu
            if pollutant_lower not in self.POLLUTANT_RANGES:
                return False, f"Unknown pollutant: {pollutant}", {}
            
            # Vérifier la concentration
            if not isinstance(concentration, (int, float)):
                return False, "Concentration must be numeric", {}
            
            if concentration < 0:
                return False, "Concentration cannot be negative", {}
            
            # Vérifier les plages normales
            ranges = self.POLLUTANT_RANGES[pollutant_lower]
            
            quality_info = {
                "pollutant": pollutant_lower,
                "concentration": concentration,
                "expected_unit": ranges["unit"],
                "is_within_normal_range": ranges["min"] <= concentration <= ranges["max"],
                "quality_level": self._assess_concentration_quality(pollutant_lower, concentration)
            }
            
            # Vérifications spéciales
            warnings = []
            
            if concentration > ranges["max"]:
                warnings.append(f"Extremely high concentration ({concentration} > {ranges['max']})")
            elif concentration > ranges["max"] * 0.8:
                warnings.append(f"Very high concentration ({concentration})")
            
            if concentration == 0:
                warnings.append("Zero concentration - verify sensor accuracy")
            
            quality_info["warnings"] = warnings
            quality_info["is_suspicious"] = len(warnings) > 0
            
            return True, "", quality_info
            
        except Exception as e:
            return False, f"Pollutant validation error: {str(e)}", {}
    
    def validate_aqi_value(self, aqi: int) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valide une valeur AQI.
        
        Args:
            aqi: Valeur AQI à valider
            
        Returns:
            Tuple (is_valid, error_message, aqi_info)
        """
        try:
            if not isinstance(aqi, (int, float)):
                return False, "AQI must be numeric", {}
            
            aqi = int(aqi)
            
            if aqi < 0:
                return False, "AQI cannot be negative", {}
            
            if aqi > 500:
                return False, "AQI above 500 is not standardized", {}
            
            # Déterminer la catégorie
            category = "unknown"
            for cat, (min_val, max_val) in self.AQI_RANGES.items():
                if min_val <= aqi <= max_val:
                    category = cat
                    break
            
            if aqi > 500:
                category = "beyond_hazardous"
            
            aqi_info = {
                "aqi": aqi,
                "category": category,
                "is_emergency_level": aqi > 300,
                "health_concern": self._get_health_concern_level(aqi)
            }
            
            return True, "", aqi_info
            
        except Exception as e:
            return False, f"AQI validation error: {str(e)}", {}
    
    def validate_timestamp(self, timestamp: Any, max_age_hours: int = 24) -> Tuple[bool, str]:
        """
        Valide un timestamp de données.
        
        Args:
            timestamp: Timestamp à valider (datetime, string ISO, ou unix)
            max_age_hours: Âge maximum acceptable en heures
            
        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            # Convertir en datetime si nécessaire
            if isinstance(timestamp, str):
                # Essayer plusieurs formats
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        dt = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return False, f"Invalid timestamp format: {timestamp}"
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                dt = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                return False, f"Unsupported timestamp type: {type(timestamp)}"
            
            # Vérifier l'âge
            now = datetime.now()
            age = now - dt
            
            if age.total_seconds() < 0:
                return False, "Timestamp is in the future"
            
            if age.total_seconds() > max_age_hours * 3600:
                return False, f"Data too old: {age.total_seconds() / 3600:.1f} hours"
            
            return True, ""
            
        except Exception as e:
            return False, f"Timestamp validation error: {str(e)}"
    
    def validate_data_source(self, source: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valide et évalue une source de données.
        
        Args:
            source: Nom de la source de données
            
        Returns:
            Tuple (is_valid, error_message, source_info)
        """
        try:
            # Sources connues et leurs caractéristiques
            known_sources = {
                "nasa_tempo": {
                    "type": "satellite",
                    "reliability": 0.95,
                    "coverage": "north_america",
                    "update_frequency": "hourly"
                },
                "openaq": {
                    "type": "ground_stations",
                    "reliability": 0.90,
                    "coverage": "global",
                    "update_frequency": "realtime"
                },
                "aqicn": {
                    "type": "hybrid",
                    "reliability": 0.88,
                    "coverage": "global",
                    "update_frequency": "hourly"
                },
                "nasa_airs": {
                    "type": "satellite", 
                    "reliability": 0.85,
                    "coverage": "global",
                    "update_frequency": "daily"
                },
                "epa_airnow": {
                    "type": "government",
                    "reliability": 0.98,
                    "coverage": "usa",
                    "update_frequency": "hourly"
                }
            }
            
            source_lower = source.lower().replace(" ", "_").replace("-", "_")
            
            if source_lower in known_sources:
                source_info = {
                    "source": source,
                    "normalized_name": source_lower,
                    "is_known": True,
                    **known_sources[source_lower]
                }
            else:
                source_info = {
                    "source": source,
                    "normalized_name": source_lower,
                    "is_known": False,
                    "type": "unknown",
                    "reliability": 0.5,  # Score par défaut pour sources inconnues
                    "coverage": "unknown",
                    "update_frequency": "unknown"
                }
            
            return True, "", source_info
            
        except Exception as e:
            return False, f"Source validation error: {str(e)}", {}
    
    def validate_complete_air_quality_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validation complète d'un objet de données de qualité de l'air.
        
        Args:
            data: Dictionnaire complet de données à valider
            
        Returns:
            Rapport de validation détaillé
        """
        validation_report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "quality_score": 1.0,
            "recommendations": []
        }
        
        try:
            # Validation des coordonnées
            if "location" in data:
                location = data["location"]
                if "latitude" in location and "longitude" in location:
                    is_valid, error = self.validate_coordinates(
                        location["latitude"], location["longitude"]
                    )
                    if not is_valid:
                        validation_report["errors"].append(f"Location: {error}")
                        validation_report["is_valid"] = False
                
            # Validation des polluants
            if "pollutants" in data:
                for pollutant_data in data["pollutants"]:
                    if "pollutant" in pollutant_data and "concentration" in pollutant_data:
                        is_valid, error, quality_info = self.validate_pollutant_data(
                            pollutant_data["pollutant"],
                            pollutant_data["concentration"]
                        )
                        
                        if not is_valid:
                            validation_report["errors"].append(f"Pollutant {pollutant_data['pollutant']}: {error}")
                            validation_report["is_valid"] = False
                        elif quality_info.get("is_suspicious"):
                            validation_report["warnings"].extend(quality_info["warnings"])
                            validation_report["quality_score"] *= 0.9
            
            # Validation AQI
            if "overall_aqi" in data:
                is_valid, error, aqi_info = self.validate_aqi_value(data["overall_aqi"])
                if not is_valid:
                    validation_report["errors"].append(f"AQI: {error}")
                    validation_report["is_valid"] = False
            
            # Validation timestamp
            if "timestamp" in data:
                is_valid, error = self.validate_timestamp(data["timestamp"])
                if not is_valid:
                    validation_report["errors"].append(f"Timestamp: {error}")
                    validation_report["is_valid"] = False
            
            # Validation des sources
            if "data_sources" in data:
                source_reliabilities = []
                for source in data["data_sources"]:
                    is_valid, error, source_info = self.validate_data_source(source)
                    if is_valid:
                        source_reliabilities.append(source_info["reliability"])
                    else:
                        validation_report["warnings"].append(f"Source {source}: {error}")
                
                # Ajuster le score de qualité basé sur la fiabilité des sources
                if source_reliabilities:
                    avg_reliability = sum(source_reliabilities) / len(source_reliabilities)
                    validation_report["quality_score"] *= avg_reliability
            
            # Génération de recommandations
            if validation_report["quality_score"] < 0.7:
                validation_report["recommendations"].append("Consider using additional data sources for better reliability")
            
            if len(data.get("data_sources", [])) < 2:
                validation_report["recommendations"].append("Use multiple data sources for cross-validation")
            
            if validation_report["warnings"]:
                validation_report["recommendations"].append("Review data quality warnings before using in critical applications")
            
            validation_report["quality_score"] = round(validation_report["quality_score"], 3)
            
        except Exception as e:
            validation_report["errors"].append(f"Validation process error: {str(e)}")
            validation_report["is_valid"] = False
            validation_report["quality_score"] = 0.0
        
        return validation_report
    
    def _assess_concentration_quality(self, pollutant: str, concentration: float) -> str:
        """Évalue la qualité d'une concentration de polluant."""
        ranges = self.POLLUTANT_RANGES[pollutant]
        
        if concentration > ranges["max"]:
            return "suspicious_high"
        elif concentration > ranges["max"] * 0.8:
            return "very_high"
        elif concentration > ranges["max"] * 0.5:
            return "high"
        elif concentration > ranges["max"] * 0.2:
            return "moderate"
        elif concentration > 0:
            return "low"
        else:
            return "suspicious_zero"
    
    def _get_health_concern_level(self, aqi: int) -> str:
        """Détermine le niveau de préoccupation sanitaire basé sur l'AQI."""
        if aqi <= 50:
            return "low"
        elif aqi <= 100:
            return "moderate"
        elif aqi <= 150:
            return "high_sensitive"
        elif aqi <= 200:
            return "high"
        elif aqi <= 300:
            return "very_high"
        else:
            return "emergency"


# Instance globale du service de validation
validation_service = DataValidationService()
#!/usr/bin/env python3
"""
🌍 SERVICE DE GÉOLOCALISATION AVANCÉ - INTÉGRATION COMPLÈTE
===========================================================
Service complet pour identification des États, pays, provinces
et intégration de tous les collecteurs de données développés.

Fonctionnalités:
- Identification précise États/Provinces/Pays
- Collecteur Open Source intégré
- Indices EPA AQI + WHO + Canada AQHI
- Sources optimisées par région
- Base de données géographiques complète
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Import des collecteurs développés
from app.collectors.open_source_collector import OpenSourceAirQualityCollector
from app.collectors.test_north_america_states import NorthAmericaAirQualityTester

logger = logging.getLogger(__name__)

@dataclass
class GeographicLocation:
    """Informations géographiques complètes d'une location"""
    latitude: float
    longitude: float
    country: str
    country_code: str
    state_province: Optional[str] = None
    state_province_code: Optional[str] = None
    city: Optional[str] = None
    region: str = "Global"
    timezone: Optional[str] = None
    optimal_data_sources: List[str] = None
    coverage_assessment: Dict[str, Any] = None

@dataclass
class AirQualityIndices:
    """Indices de qualité de l'air complets"""
    epa_aqi: Optional[int] = None
    epa_category: Optional[str] = None
    who_compliance: Dict[str, str] = None
    canada_aqhi: Optional[float] = None
    canada_aqhi_category: Optional[str] = None
    health_recommendations: List[str] = None

@dataclass
class ComprehensiveAirQualityData:
    """Données complètes de qualité de l'air avec localisation"""
    location: GeographicLocation
    timestamp: datetime
    raw_data: Dict[str, Any]
    indices: AirQualityIndices
    data_sources_used: List[str]
    quality_assessment: Dict[str, Any]
    recommendations: List[str]

class AdvancedGeolocationService:
    """
    Service avancé de géolocalisation et collecte de données
    Intègre tous les développements précédents
    """
    
    def __init__(self):
        """Initialisation avec base de données géographiques complète"""
        
        # Base de données des États/Provinces d'Amérique du Nord
        self.north_america_database = {
            # États-Unis
            "USA": {
                "country_code": "US",
                "timezone_base": "America/",
                "states": {
                    "California": {
                        "code": "CA",
                        "bounds": {"lat": (32.5, 42.0), "lon": (-124.5, -114.1)},
                        "major_cities": ["Los Angeles", "San Francisco", "San Diego"],
                        "timezone": "America/Los_Angeles",
                        "aqi_standards": "EPA"
                    },
                    "Texas": {
                        "code": "TX", 
                        "bounds": {"lat": (25.8, 36.5), "lon": (-106.6, -93.5)},
                        "major_cities": ["Houston", "Dallas", "Austin", "San Antonio"],
                        "timezone": "America/Chicago",
                        "aqi_standards": "EPA"
                    },
                    "Florida": {
                        "code": "FL",
                        "bounds": {"lat": (24.4, 31.0), "lon": (-87.6, -80.0)},
                        "major_cities": ["Miami", "Tampa", "Orlando", "Jacksonville"],
                        "timezone": "America/New_York",
                        "aqi_standards": "EPA"
                    },
                    "New York": {
                        "code": "NY",
                        "bounds": {"lat": (40.5, 45.0), "lon": (-79.8, -71.9)},
                        "major_cities": ["New York City", "Buffalo", "Rochester", "Syracuse"],
                        "timezone": "America/New_York",
                        "aqi_standards": "EPA"
                    },
                    "Illinois": {
                        "code": "IL",
                        "bounds": {"lat": (36.9, 42.5), "lon": (-91.5, -87.0)},
                        "major_cities": ["Chicago", "Rockford", "Peoria", "Springfield"],
                        "timezone": "America/Chicago",
                        "aqi_standards": "EPA"
                    },
                    "Pennsylvania": {
                        "code": "PA",
                        "bounds": {"lat": (39.7, 42.3), "lon": (-80.5, -74.7)},
                        "major_cities": ["Philadelphia", "Pittsburgh", "Allentown"],
                        "timezone": "America/New_York",
                        "aqi_standards": "EPA"
                    },
                    "Ohio": {
                        "code": "OH",
                        "bounds": {"lat": (38.4, 42.3), "lon": (-84.8, -80.5)},
                        "major_cities": ["Columbus", "Cleveland", "Cincinnati"],
                        "timezone": "America/New_York",
                        "aqi_standards": "EPA"
                    },
                    "Georgia": {
                        "code": "GA",
                        "bounds": {"lat": (30.4, 35.0), "lon": (-85.6, -81.0)},
                        "major_cities": ["Atlanta", "Augusta", "Columbus", "Savannah"],
                        "timezone": "America/New_York",
                        "aqi_standards": "EPA"
                    },
                    "North Carolina": {
                        "code": "NC",
                        "bounds": {"lat": (33.8, 36.6), "lon": (-84.3, -75.5)},
                        "major_cities": ["Charlotte", "Raleigh", "Greensboro"],
                        "timezone": "America/New_York",
                        "aqi_standards": "EPA"
                    },
                    "Michigan": {
                        "code": "MI",
                        "bounds": {"lat": (41.7, 48.3), "lon": (-90.4, -82.1)},
                        "major_cities": ["Detroit", "Grand Rapids", "Warren"],
                        "timezone": "America/Detroit",
                        "aqi_standards": "EPA"
                    }
                }
            },
            
            # Canada
            "Canada": {
                "country_code": "CA",
                "timezone_base": "America/",
                "provinces": {
                    "Ontario": {
                        "code": "ON",
                        "bounds": {"lat": (41.7, 56.9), "lon": (-95.2, -74.3)},
                        "major_cities": ["Toronto", "Ottawa", "Hamilton", "London"],
                        "timezone": "America/Toronto",
                        "aqi_standards": "AQHI"
                    },
                    "Quebec": {
                        "code": "QC",
                        "bounds": {"lat": (45.0, 62.6), "lon": (-79.8, -57.1)},
                        "major_cities": ["Montreal", "Quebec City", "Laval"],
                        "timezone": "America/Montreal",
                        "aqi_standards": "AQHI"
                    },
                    "British Columbia": {
                        "code": "BC",
                        "bounds": {"lat": (48.3, 60.0), "lon": (-139.1, -114.0)},
                        "major_cities": ["Vancouver", "Victoria", "Surrey"],
                        "timezone": "America/Vancouver",
                        "aqi_standards": "AQHI"
                    },
                    "Alberta": {
                        "code": "AB",
                        "bounds": {"lat": (49.0, 60.0), "lon": (-120.0, -110.0)},
                        "major_cities": ["Calgary", "Edmonton", "Red Deer"],
                        "timezone": "America/Edmonton",
                        "aqi_standards": "AQHI"
                    },
                    "Manitoba": {
                        "code": "MB",
                        "bounds": {"lat": (49.0, 60.0), "lon": (-102.0, -89.0)},
                        "major_cities": ["Winnipeg", "Brandon", "Steinbach"],
                        "timezone": "America/Winnipeg",
                        "aqi_standards": "AQHI"
                    },
                    "Saskatchewan": {
                        "code": "SK",
                        "bounds": {"lat": (49.0, 60.0), "lon": (-110.0, -102.0)},
                        "major_cities": ["Saskatoon", "Regina", "Prince Albert"],
                        "timezone": "America/Regina",
                        "aqi_standards": "AQHI"
                    }
                }
            }
        }
        
        # Base de données régions mondiales élargie
        self.global_regions = {
            "North America": {
                "bounds": {"lat": (15, 72), "lon": (-170, -50)},
                "countries": ["USA", "Canada", "Mexico"],
                "optimal_sources": ["NASA_TEMPO", "EPA_AIRNOW", "OPENAQ", "AQICN"],
                "primary_standards": "EPA_AQI"
            },
            "Europe": {
                "bounds": {"lat": (35, 72), "lon": (-15, 40)},
                "countries": ["France", "Germany", "UK", "Spain", "Italy"],
                "optimal_sources": ["ESA_SENTINEL5P", "SENSOR_COMMUNITY", "OPENAQ", "AQICN"],
                "primary_standards": "WHO"
            },
            "South America": {
                "bounds": {"lat": (-60, 15), "lon": (-85, -30)},
                "countries": ["Brazil", "Argentina", "Chile", "Colombia"],
                "optimal_sources": ["INPE_CPTEC", "ESA_SENTINEL5P", "OPENAQ", "AQICN"],
                "primary_standards": "WHO"
            },
            "Asia": {
                "bounds": {"lat": (-10, 55), "lon": (60, 180)},
                "countries": ["China", "Japan", "India", "South Korea"],
                "optimal_sources": ["NASA_AIRS", "ESA_SENTINEL5P", "OPENAQ", "AQICN"],
                "primary_standards": "WHO"
            },
            "Global": {
                "bounds": {"lat": (-90, 90), "lon": (-180, 180)},
                "countries": ["*"],
                "optimal_sources": ["NASA_MERRA2", "ESA_SENTINEL5P", "OPENAQ", "AQICN"],
                "primary_standards": "WHO"
            }
        }
        
        # Initialiser les collecteurs
        self.open_source_collector = OpenSourceAirQualityCollector()
        self.north_america_tester = NorthAmericaAirQualityTester()
        
        print("🌍 SERVICE GÉOLOCALISATION AVANCÉ INITIALISÉ")
        print("✅ Base de données 16 États/Provinces Amérique du Nord")
        print("✅ Identification automatique régions mondiales")
        print("✅ Collecteurs open source intégrés")
        print("✅ Standards EPA AQI + WHO + Canada AQHI")
    
    def identify_location(self, latitude: float, longitude: float) -> GeographicLocation:
        """
        Identification complète d'une location géographique
        avec État/Province, pays, région et sources optimales
        """
        
        # Identifier le pays et l'État/Province pour Amérique du Nord
        country = "Unknown"
        country_code = "UN"
        state_province = None
        state_province_code = None
        city = None
        timezone = None
        aqi_standards = "WHO"
        
        # Vérification Amérique du Nord détaillée
        for country_name, country_data in self.north_america_database.items():
            if country_name == "USA":
                for state_name, state_data in country_data["states"].items():
                    lat_bounds = state_data["bounds"]["lat"]
                    lon_bounds = state_data["bounds"]["lon"]
                    
                    if (lat_bounds[0] <= latitude <= lat_bounds[1] and 
                        lon_bounds[0] <= longitude <= lon_bounds[1]):
                        country = "United States"
                        country_code = "US"
                        state_province = state_name
                        state_province_code = state_data["code"]
                        timezone = state_data["timezone"]
                        aqi_standards = "EPA"
                        # Trouver la ville la plus proche (simplifiée)
                        city = state_data["major_cities"][0]  # Ville principale
                        break
                        
            elif country_name == "Canada":
                for province_name, province_data in country_data["provinces"].items():
                    lat_bounds = province_data["bounds"]["lat"]
                    lon_bounds = province_data["bounds"]["lon"]
                    
                    if (lat_bounds[0] <= latitude <= lat_bounds[1] and 
                        lon_bounds[0] <= longitude <= lon_bounds[1]):
                        country = "Canada"
                        country_code = "CA"
                        state_province = province_name
                        state_province_code = province_data["code"]
                        timezone = province_data["timezone"]
                        aqi_standards = "AQHI"
                        city = province_data["major_cities"][0]
                        break
        
        # Identifier la région globale
        region = self.identify_global_region(latitude, longitude)
        
        # Sources optimales selon la région
        region_data = self.global_regions.get(region, self.global_regions["Global"])
        optimal_sources = region_data["optimal_sources"]
        
        # Évaluation de la couverture
        coverage_assessment = self.assess_data_coverage(latitude, longitude, region)
        
        return GeographicLocation(
            latitude=latitude,
            longitude=longitude,
            country=country,
            country_code=country_code,
            state_province=state_province,
            state_province_code=state_province_code,
            city=city,
            region=region,
            timezone=timezone,
            optimal_data_sources=optimal_sources,
            coverage_assessment=coverage_assessment
        )
    
    def identify_global_region(self, latitude: float, longitude: float) -> str:
        """Identification de la région globale"""
        
        for region_name, region_data in self.global_regions.items():
            if region_name == "Global":
                continue
                
            bounds = region_data["bounds"]
            if (bounds["lat"][0] <= latitude <= bounds["lat"][1] and 
                bounds["lon"][0] <= longitude <= bounds["lon"][1]):
                return region_name
        
        return "Global"
    
    def assess_data_coverage(self, latitude: float, longitude: float, region: str) -> Dict[str, Any]:
        """Évaluation de la couverture des données pour une location"""
        
        coverage = {
            "nasa_tempo": False,
            "ground_stations": "Unknown",
            "satellite_coverage": "Partial",
            "recommended_confidence": 0.7,
            "data_availability_score": 0.6
        }
        
        # Couverture NASA TEMPO (Amérique du Nord)
        if 15 <= latitude <= 70 and -170 <= longitude <= -50:
            coverage["nasa_tempo"] = True
            coverage["recommended_confidence"] = 0.9
            coverage["data_availability_score"] = 0.9
        
        # Estimation des stations au sol selon la région
        if region in ["North America", "Europe"]:
            coverage["ground_stations"] = "Dense"
            coverage["data_availability_score"] += 0.2
        elif region in ["South America", "Asia"]:
            coverage["ground_stations"] = "Moderate"
            coverage["data_availability_score"] += 0.1
        else:
            coverage["ground_stations"] = "Sparse"
        
        # Couverture satellite globale
        coverage["satellite_coverage"] = "Global"
        
        return coverage
    
    async def get_comprehensive_air_quality(self, latitude: float, longitude: float) -> ComprehensiveAirQualityData:
        """
        Collecte complète de données de qualité de l'air
        avec identification géographique et indices calculés
        """
        
        # Identification géographique complète
        location = self.identify_location(latitude, longitude)
        
        print(f"\n🌍 COLLECTE COMPLÈTE: {location.city or 'Location'}, {location.state_province or location.country}")
        print(f"📍 Coordonnées: {latitude:.4f}, {longitude:.4f}")
        print(f"🗺️ Région: {location.region}")
        
        # Collecte des données selon la région
        if location.region == "North America" and location.state_province:
            # Utiliser le testeur spécialisé Amérique du Nord
            raw_data = await self.collect_north_america_data(location)
        else:
            # Utiliser le collecteur open source global
            raw_data = await self.open_source_collector.collect_free_data(latitude, longitude)
        
        # Calculer les indices selon les standards locaux
        indices = await self.calculate_comprehensive_indices(raw_data, location)
        
        # Évaluation de la qualité des données
        quality_assessment = self.assess_data_quality(raw_data, location)
        
        # Recommandations contextuelles
        recommendations = self.generate_recommendations(raw_data, indices, location)
        
        return ComprehensiveAirQualityData(
            location=location,
            timestamp=datetime.utcnow(),
            raw_data=raw_data,
            indices=indices,
            data_sources_used=raw_data.get("sources_active", []),
            quality_assessment=quality_assessment,
            recommendations=recommendations
        )
    
    async def collect_north_america_data(self, location: GeographicLocation) -> Dict[str, Any]:
        """Collecte spécialisée pour Amérique du Nord avec indices détaillés"""
        
        try:
            # Utiliser le testeur spécialisé
            location_info = {
                "coords": (location.latitude, location.longitude),
                "city": location.city or "Unknown",
                "country": location.country
            }
            
            result = await self.north_america_tester.test_north_america_state(
                location.state_province or "Unknown", 
                location_info
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in North America data collection: {e}")
            # Fallback vers collecteur open source
            return await self.open_source_collector.collect_free_data(
                location.latitude, location.longitude
            )
    
    async def calculate_comprehensive_indices(self, raw_data: Dict[str, Any], location: GeographicLocation) -> AirQualityIndices:
        """Calcul des indices complets selon les standards locaux"""
        
        indices = AirQualityIndices()
        
        try:
            # Si données Amérique du Nord avec indices déjà calculés
            if "epa_aqi_global" in raw_data:
                indices.epa_aqi = raw_data["epa_aqi_global"]
                indices.epa_category = raw_data.get("epa_category_global")
                
                if location.country == "Canada":
                    indices.canada_aqhi = raw_data.get("canada_aqhi")
                    indices.canada_aqhi_category = raw_data.get("canada_aqhi_category")
                
                # Extraire compliance WHO des détails polluants
                who_compliance = {}
                for pollutant_data in raw_data.get("pollutant_indices", []):
                    pollutant = pollutant_data.get("pollutant")
                    who_assessment = pollutant_data.get("who_assessment")
                    if pollutant and who_assessment:
                        who_compliance[pollutant] = who_assessment
                
                indices.who_compliance = who_compliance
            
            # Si données open source, calculer les indices
            elif "fused_pollutants" in raw_data:
                indices = await self.calculate_indices_from_fused_data(raw_data, location)
            
            # Recommandations santé
            indices.health_recommendations = self.generate_health_recommendations(indices, location)
            
        except Exception as e:
            logger.error(f"Error calculating indices: {e}")
        
        return indices
    
    async def calculate_indices_from_fused_data(self, raw_data: Dict[str, Any], location: GeographicLocation) -> AirQualityIndices:
        """Calcul des indices à partir des données fusionnées du collecteur open source"""
        
        indices = AirQualityIndices()
        fused_data = raw_data.get("fused_pollutants", {})
        
        if not fused_data:
            return indices
        
        # Calculer EPA AQI (maximum des AQI individuels)
        max_aqi = 0
        aqi_category = "Good"
        who_compliance = {}
        
        for pollutant, data in fused_data.items():
            concentration = data.get("value", 0)
            
            # Calcul AQI EPA simplifié
            aqi, category = self.calculate_simple_aqi(pollutant, concentration)
            if aqi > max_aqi:
                max_aqi = aqi
                aqi_category = category
            
            # Évaluation WHO
            who_assessment = self.assess_who_simple(pollutant, concentration)
            who_compliance[pollutant] = who_assessment
        
        indices.epa_aqi = max_aqi
        indices.epa_category = aqi_category
        indices.who_compliance = who_compliance
        
        # Calcul AQHI Canada si applicable
        if location.country == "Canada":
            aqhi_score = 0
            for pollutant in ["NO2", "O3", "PM2.5"]:
                if pollutant in fused_data:
                    # Coefficients AQHI simplifiés
                    coeff = {"NO2": 0.0005, "O3": 0.0009, "PM2.5": 0.0005}.get(pollutant, 0)
                    aqhi_score += coeff * fused_data[pollutant].get("value", 0) * 1000
            
            indices.canada_aqhi = round(aqhi_score, 1)
            
            if aqhi_score <= 3:
                indices.canada_aqhi_category = "Low Risk"
            elif aqhi_score <= 6:
                indices.canada_aqhi_category = "Moderate Risk"
            elif aqhi_score <= 10:
                indices.canada_aqhi_category = "High Risk"
            else:
                indices.canada_aqhi_category = "Very High Risk"
        
        return indices
    
    def calculate_simple_aqi(self, pollutant: str, concentration: float) -> Tuple[int, str]:
        """Calcul AQI simplifié"""
        
        # Points de rupture EPA simplifiés
        if pollutant == "PM2.5":
            if concentration <= 12:
                return int(concentration * 50 / 12), "Good"
            elif concentration <= 35.4:
                return int(50 + (concentration - 12) * 50 / 23.4), "Moderate"
            else:
                return min(200, int(100 + (concentration - 35.4) * 50 / 20)), "Unhealthy for Sensitive Groups"
        
        elif pollutant == "O3":
            if concentration <= 54:
                return int(concentration * 50 / 54), "Good"
            elif concentration <= 70:
                return int(50 + (concentration - 54) * 50 / 16), "Moderate"
            else:
                return min(200, int(100 + (concentration - 70) * 50 / 15)), "Unhealthy for Sensitive Groups"
        
        # Autres polluants - estimation
        return min(150, int(concentration * 2)), "Moderate"
    
    def assess_who_simple(self, pollutant: str, concentration: float) -> str:
        """Évaluation WHO simplifiée"""
        
        who_limits = {
            "PM2.5": 15,  # 24h guideline
            "PM10": 45,
            "NO2": 25,
            "O3": 100
        }
        
        limit = who_limits.get(pollutant, 100)
        ratio = concentration / limit
        
        if ratio <= 1.0:
            return f"✅ WHO Compliant ({ratio:.1f}x)"
        elif ratio <= 2.0:
            return f"⚠️ WHO Exceedance ({ratio:.1f}x)"
        else:
            return f"🔴 Significant Exceedance ({ratio:.1f}x)"
    
    def assess_data_quality(self, raw_data: Dict[str, Any], location: GeographicLocation) -> Dict[str, Any]:
        """Évaluation de la qualité des données collectées"""
        
        quality = {
            "overall_score": 0.7,
            "source_diversity": 0.5,
            "temporal_coverage": "Current",
            "spatial_resolution": "Moderate",
            "confidence_level": "Good"
        }
        
        # Évaluation selon les données disponibles
        if "sources_active" in raw_data:
            active_sources = raw_data["sources_active"]
            total_sources = raw_data.get("sources_total", 5)
            
            quality["overall_score"] = active_sources / total_sources
            quality["source_diversity"] = min(1.0, active_sources / 3)
            
            if active_sources >= 4:
                quality["confidence_level"] = "Excellent"
            elif active_sources >= 2:
                quality["confidence_level"] = "Good"
            else:
                quality["confidence_level"] = "Limited"
        
        # Ajustement selon la région
        if location.coverage_assessment.get("nasa_tempo"):
            quality["spatial_resolution"] = "High"
            quality["overall_score"] += 0.1
        
        return quality
    
    def generate_health_recommendations(self, indices: AirQualityIndices, location: GeographicLocation) -> List[str]:
        """Génération de recommandations santé selon les indices"""
        
        recommendations = []
        
        # Recommandations selon EPA AQI
        if indices.epa_aqi:
            if indices.epa_aqi <= 50:
                recommendations.append("🟢 Qualité excellente - Activités extérieures recommandées")
            elif indices.epa_aqi <= 100:
                recommendations.append("🟡 Qualité modérée - Groupes sensibles: limiter activités prolongées")
            elif indices.epa_aqi <= 150:
                recommendations.append("🟠 Attention groupes sensibles - Enfants et personnes âgées: rester à l'intérieur")
            else:
                recommendations.append("🔴 Qualité malsaine - Limiter toutes activités extérieures")
        
        # Recommandations selon AQHI Canada
        if indices.canada_aqhi and location.country == "Canada":
            if indices.canada_aqhi <= 3:
                recommendations.append("🇨🇦 AQHI Bas - Activités normales")
            elif indices.canada_aqhi <= 6:
                recommendations.append("🇨🇦 AQHI Modéré - Groupes sensibles: réduire activités intenses")
            else:
                recommendations.append("🇨🇦 AQHI Élevé - Éviter activités extérieures intenses")
        
        # Recommandations selon WHO
        if indices.who_compliance:
            violations = [p for p, status in indices.who_compliance.items() if "Exceedance" in status]
            if violations:
                recommendations.append(f"🌍 WHO: Dépassements détectés ({', '.join(violations)})")
        
        return recommendations
    
    def generate_recommendations(self, raw_data: Dict[str, Any], indices: AirQualityIndices, location: GeographicLocation) -> List[str]:
        """Génération de recommandations complètes"""
        
        recommendations = []
        
        # Recommandations santé
        health_recs = self.generate_health_recommendations(indices, location)
        recommendations.extend(health_recs)
        
        # Recommandations techniques
        quality_assessment = raw_data.get("quality_assessment", {})
        
        if quality_assessment.get("overall_quality", 0) < 0.7:
            recommendations.append("🔧 Qualité données limitée - Considérer sources additionnelles")
        
        if location.coverage_assessment.get("nasa_tempo"):
            recommendations.append("🛰️ Couverture NASA TEMPO optimale disponible")
        
        # Recommandations géographiques
        if location.region == "North America":
            recommendations.append("🇺🇸🇨🇦 Standards EPA AQI/AQHI Canada appliqués")
        else:
            recommendations.append("🌍 Standards OMS appliqués")
        
        return recommendations

# Instance globale du service
advanced_geolocation_service = AdvancedGeolocationService()

# Fonctions utilitaires pour l'API
async def get_location_air_quality(latitude: float, longitude: float) -> ComprehensiveAirQualityData:
    """API wrapper pour obtenir données complètes selon coordonnées"""
    return await advanced_geolocation_service.get_comprehensive_air_quality(latitude, longitude)

def identify_location_details(latitude: float, longitude: float) -> GeographicLocation:
    """API wrapper pour identification géographique"""
    return advanced_geolocation_service.identify_location(latitude, longitude)

async def get_state_province_air_quality(state_province: str, country: str = "USA") -> Optional[ComprehensiveAirQualityData]:
    """Obtenir données de qualité de l'air par État/Province"""
    
    # Rechercher les coordonnées de l'État/Province
    coords = None
    
    if country.upper() in ["USA", "US", "UNITED STATES"]:
        for state_name, state_data in advanced_geolocation_service.north_america_database["USA"]["states"].items():
            if state_name.lower() == state_province.lower():
                # Utiliser le centre approximatif de l'État
                lat_bounds = state_data["bounds"]["lat"]
                lon_bounds = state_data["bounds"]["lon"]
                coords = (
                    (lat_bounds[0] + lat_bounds[1]) / 2,
                    (lon_bounds[0] + lon_bounds[1]) / 2
                )
                break
    
    elif country.upper() in ["CANADA", "CA"]:
        for province_name, province_data in advanced_geolocation_service.north_america_database["Canada"]["provinces"].items():
            if province_name.lower() == state_province.lower():
                lat_bounds = province_data["bounds"]["lat"]
                lon_bounds = province_data["bounds"]["lon"]
                coords = (
                    (lat_bounds[0] + lat_bounds[1]) / 2,
                    (lon_bounds[0] + lon_bounds[1]) / 2
                )
                break
    
    if coords:
        return await get_location_air_quality(coords[0], coords[1])
    
    return None

if __name__ == "__main__":
    # Test du service
    async def test_service():
        print("🧪 TEST DU SERVICE GÉOLOCALISATION AVANCÉ")
        
        # Test Los Angeles
        result = await get_location_air_quality(34.0522, -118.2437)
        print(f"\n📍 {result.location.city}, {result.location.state_province}")
        print(f"🇺🇸 EPA AQI: {result.indices.epa_aqi}")
        print(f"🌍 Région: {result.location.region}")
        
        # Test Toronto  
        result = await get_location_air_quality(43.6532, -79.3832)
        print(f"\n📍 {result.location.city}, {result.location.state_province}")
        print(f"🇨🇦 AQHI: {result.indices.canada_aqhi}")
        
        # Test par État
        result = await get_state_province_air_quality("California", "USA")
        if result:
            print(f"\n🏛️ État: {result.location.state_province}")
            print(f"🎯 Sources: {len(result.data_sources_used)}")
    
    asyncio.run(test_service())
"""
Enhanced NASA TEMPO Real-Time Air Quality Service
Integrates all real data sources for comprehensive air quality data
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from geopy.geocoders import Nominatim

from ..connectors.enhanced_realtime_connector import EnhancedRealTimeConnector

logger = logging.getLogger(__name__)

class EnhancedNASATempoService:
    """
    Enhanced service that provides comprehensive air quality data from:
    - NASA TEMPO satellite
    - OpenAQ global network  
    - NASA ground stations
    - International space agencies
    - WHO guidelines compliance
    """
    
    def __init__(self, nasa_username=None, nasa_password=None, nasa_token=None):
        self.connector = EnhancedRealTimeConnector(nasa_username, nasa_password, nasa_token)
        self.geocoder = Nominatim(user_agent="nasa-tempo-api")
        
        # WHO guidelines for health assessment
        self.who_guidelines = {
            'pm25': {'annual': 5.0, 'daily': 15.0},
            'pm10': {'annual': 15.0, 'daily': 45.0},
            'no2': {'annual': 10.0, 'daily': 25.0},
            'o3': {'8h': 100.0},
            'so2': {'daily': 40.0}
        }
    
    async def get_complete_location_data(
        self, 
        latitude: float, 
        longitude: float, 
        include_forecast: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive air quality data for a location from all available sources
        
        Returns:
        - Real-time measurements from multiple sources
        - WHO guideline compliance
        - Health recommendations
        - Data source attribution
        """
        try:
            # Get location name
            location_name = await self._get_location_name(latitude, longitude)
            
            # Get comprehensive air quality data
            async with self.connector as conn:
                air_quality_data = await conn.get_comprehensive_data(latitude, longitude)
            
            # Process and enhance the data
            enhanced_data = await self._enhance_air_quality_data(
                air_quality_data, latitude, longitude, location_name
            )
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error getting complete location data: {e}")
            return await self._get_fallback_response(latitude, longitude)
    
    async def _enhance_air_quality_data(
        self, 
        raw_data: Dict, 
        latitude: float, 
        longitude: float, 
        location_name: str
    ) -> Dict[str, Any]:
        """Enhance raw data with WHO compliance, health info, and formatting"""
        
        enhanced = {
            'location': {
                'name': location_name,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data_sources': raw_data.get('sources', []),
            'aqi': self._format_aqi_data(raw_data.get('aqi', {})),
            'pollutants': {},
            'who_compliance': {},
            'health_recommendations': [],
            'coverage_info': {}
        }
        
        # Process pollutant data
        for pollutant, data in raw_data.get('pollutants', {}).items():
            enhanced['pollutants'][pollutant] = {
                'value': data['value'],
                'unit': data['unit'],
                'source': data['source'],
                'quality': data.get('quality', 'UNKNOWN'),
                'who_guideline': self._get_who_guideline(pollutant),
                'exceeds_who': self._exceeds_who_guideline(pollutant, data['value'])
            }
            
            # WHO compliance assessment
            enhanced['who_compliance'][pollutant] = self._assess_who_compliance(pollutant, data['value'])
        
        # Generate health recommendations
        enhanced['health_recommendations'] = self._generate_health_recommendations(enhanced['pollutants'])
        
        # Add coverage information
        enhanced['coverage_info'] = self._get_coverage_info(latitude, longitude)
        
        # Add data quality assessment
        enhanced['data_quality'] = self._assess_data_quality(raw_data)
        
        return enhanced
    
    def _format_aqi_data(self, aqi_data: Dict) -> Dict[str, Any]:
        """Format AQI data with proper structure"""
        if not aqi_data:
            return {'value': None, 'category': 'Unknown'}
        
        return {
            'value': aqi_data.get('value'),
            'category': aqi_data.get('category', {}).get('level', 'Unknown'),
            'color': aqi_data.get('category', {}).get('color', '#808080'),
            'dominant_pollutant': aqi_data.get('dominant_pollutant', 'unknown')
        }
    
    def _get_who_guideline(self, pollutant: str) -> Dict[str, Any]:
        """Get WHO guideline for pollutant"""
        if pollutant in self.who_guidelines:
            return self.who_guidelines[pollutant]
        return {}
    
    def _exceeds_who_guideline(self, pollutant: str, value: float) -> bool:
        """Check if value exceeds WHO guidelines"""
        if pollutant not in self.who_guidelines:
            return False
        
        guidelines = self.who_guidelines[pollutant]
        
        # Check against daily guideline (most restrictive for real-time data)
        if 'daily' in guidelines:
            return value > guidelines['daily']
        elif 'annual' in guidelines:
            return value > guidelines['annual']
        elif '8h' in guidelines:
            return value > guidelines['8h']
        
        return False
    
    def _assess_who_compliance(self, pollutant: str, value: float) -> Dict[str, Any]:
        """Assess compliance with WHO guidelines"""
        if pollutant not in self.who_guidelines:
            return {'status': 'no_guideline', 'message': 'No WHO guideline available'}
        
        guidelines = self.who_guidelines[pollutant]
        exceeds = self._exceeds_who_guideline(pollutant, value)
        
        if exceeds:
            # Calculate how much it exceeds
            daily_limit = guidelines.get('daily') or guidelines.get('annual') or guidelines.get('8h')
            if daily_limit:
                excess_factor = value / daily_limit
                return {
                    'status': 'exceeds',
                    'message': f'Exceeds WHO guideline by {excess_factor:.1f}x',
                    'guideline_value': daily_limit,
                    'excess_factor': round(excess_factor, 2)
                }
        
        return {
            'status': 'compliant',
            'message': 'Within WHO guidelines',
            'guideline_value': guidelines.get('daily') or guidelines.get('annual') or guidelines.get('8h')
        }
    
    def _generate_health_recommendations(self, pollutants: Dict) -> List[str]:
        """Generate health recommendations based on pollution levels"""
        recommendations = []
        
        # Check each pollutant for health concerns
        for pollutant, data in pollutants.items():
            if data.get('exceeds_who'):
                if pollutant == 'pm25':
                    recommendations.append("High PM2.5: Limit outdoor activities, especially for sensitive groups")
                elif pollutant == 'no2':
                    recommendations.append("Elevated NO2: Avoid busy roads and high-traffic areas")
                elif pollutant == 'o3':
                    recommendations.append("High ozone: Limit outdoor exercise during midday hours")
                elif pollutant == 'pm10':
                    recommendations.append("High PM10: Consider wearing a mask outdoors")
        
        # General recommendations based on AQI
        if not recommendations:
            recommendations.append("Air quality is acceptable for outdoor activities")
        
        # Add sensitive group warnings if needed
        high_pollution = any(data.get('exceeds_who') for data in pollutants.values())
        if high_pollution:
            recommendations.append("Sensitive groups (children, elderly, respiratory conditions) should take extra precautions")
        
        return recommendations
    
    def _get_coverage_info(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get information about data coverage for the location"""
        info = {
            'tempo_coverage': self.connector.is_in_tempo_coverage(latitude, longitude),
            'global_network_coverage': True,  # OpenAQ has global coverage
            'region': self._get_region(latitude, longitude)
        }
        
        # Add specific coverage notes
        if info['tempo_coverage']:
            info['note'] = 'Location has NASA TEMPO satellite coverage for enhanced air quality monitoring'
        else:
            info['note'] = 'Location outside TEMPO coverage; relying on ground stations and other satellites'
        
        return info
    
    def _get_region(self, latitude: float, longitude: float) -> str:
        """Determine geographic region"""
        if 15 <= latitude <= 70 and -140 <= longitude <= -40:
            return 'North America'
        elif 35 <= latitude <= 70 and -10 <= longitude <= 40:
            return 'Europe'
        elif -40 <= latitude <= 40 and 60 <= longitude <= 150:
            return 'Asia-Pacific'
        elif -35 <= latitude <= 15 and -75 <= longitude <= -30:
            return 'South America'
        elif -35 <= latitude <= 35 and -20 <= longitude <= 55:
            return 'Africa'
        else:
            return 'Other'
    
    def _assess_data_quality(self, raw_data: Dict) -> Dict[str, Any]:
        """Assess overall data quality"""
        quality_score = 0
        total_sources = 0
        
        # Score based on data sources
        sources = raw_data.get('sources', [])
        if 'NASA TEMPO Satellite' in sources:
            quality_score += 40
        if 'OpenAQ Global Network' in sources:
            quality_score += 30
        
        # Score based on pollutant coverage
        pollutants = raw_data.get('pollutants', {})
        essential_pollutants = ['pm25', 'no2', 'o3']
        covered_essential = sum(1 for p in essential_pollutants if p in pollutants)
        quality_score += (covered_essential / len(essential_pollutants)) * 30
        
        # Determine quality level
        if quality_score >= 80:
            level = 'EXCELLENT'
        elif quality_score >= 60:
            level = 'GOOD'
        elif quality_score >= 40:
            level = 'FAIR'
        else:
            level = 'LIMITED'
        
        return {
            'score': min(100, quality_score),
            'level': level,
            'sources_count': len(sources),
            'pollutants_count': len(pollutants)
        }
    
    async def _get_location_name(self, latitude: float, longitude: float) -> str:
        """Get human-readable location name"""
        try:
            location = self.geocoder.reverse((latitude, longitude), timeout=5)
            if location:
                # Extract meaningful location name
                address = location.raw.get('address', {})
                city = address.get('city') or address.get('town') or address.get('village')
                state = address.get('state')
                country = address.get('country')
                
                if city and state:
                    return f"{city}, {state}"
                elif city and country:
                    return f"{city}, {country}"
                elif state and country:
                    return f"{state}, {country}"
                elif country:
                    return country
                else:
                    return f"{latitude:.3f}, {longitude:.3f}"
            else:
                return f"{latitude:.3f}, {longitude:.3f}"
        except Exception as e:
            logger.warning(f"Geocoding failed: {e}")
            return f"{latitude:.3f}, {longitude:.3f}"
    
    async def _get_fallback_response(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Generate fallback response when all data sources fail"""
        location_name = await self._get_location_name(latitude, longitude)
        
        return {
            'location': {
                'name': location_name,
                'coordinates': {
                    'latitude': latitude,
                    'longitude': longitude
                }
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': 'Data sources temporarily unavailable',
            'data_sources': [],
            'aqi': {'value': None, 'category': 'Unknown'},
            'pollutants': {},
            'who_compliance': {},
            'health_recommendations': ['Unable to assess air quality at this time. Please try again later.'],
            'coverage_info': {
                'tempo_coverage': self.connector.is_in_tempo_coverage(latitude, longitude),
                'note': 'Data sources temporarily unavailable'
            },
            'data_quality': {'level': 'UNAVAILABLE', 'score': 0}
        }
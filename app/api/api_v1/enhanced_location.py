"""
Enhanced Location API with Real-Time Multi-Source Data Integration
Uses NASA TEMPO, OpenAQ, WHO guidelines, and international data sources
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import os

from app.services.enhanced_tempo_service import EnhancedNASATempoService

router = APIRouter()

# Initialize enhanced service with NASA credentials
enhanced_service = EnhancedNASATempoService(
    nasa_username=os.getenv('NASA_EARTHDATA_USERNAME'),
    nasa_password=os.getenv('NASA_EARTHDATA_PASSWORD'),
    nasa_token=os.getenv('NASA_EARTHDATA_TOKEN')
)

@router.get("/location/comprehensive")
async def get_comprehensive_location_data(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees"),
    include_forecast: Optional[bool] = Query(False, description="Include weather forecast data")
):
    """
    Get comprehensive air quality data from multiple real-time sources:
    
    **Data Sources:**
    - 🛰️ NASA TEMPO Satellite (North America)
    - 🌍 OpenAQ Global Network (150+ countries)
    - 🔬 NASA Ground Stations (Pandora, TOLNet)
    - 🇨🇦 CSA OSIRIS (Canada/Arctic)
    - 🇧🇷 Brazilian SEEG/CPTEC (South America)
    - 🏥 WHO Air Quality Guidelines (2021)
    
    **Returns:**
    - Real-time pollutant concentrations
    - WHO guideline compliance analysis
    - Health impact recommendations
    - Multi-source data quality assessment
    - Regional coverage information
    
    **Example:**
    ```
    GET /location/comprehensive?latitude=43.6532&longitude=-79.3832
    ```
    """
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
        
        # Get comprehensive data from all sources
        comprehensive_data = await enhanced_service.get_complete_location_data(
            latitude=latitude,
            longitude=longitude,
            include_forecast=include_forecast
        )
        
        return comprehensive_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving comprehensive air quality data: {str(e)}"
        )

@router.get("/location/tempo-coverage")
async def check_tempo_coverage(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees")
):
    """
    Check if a location is within NASA TEMPO satellite coverage area.
    
    **TEMPO Coverage:**
    - Geostationary satellite over North America
    - Latitude: 15°N to 70°N
    - Longitude: 140°W to 40°W
    - Hourly daylight observations
    
    **Returns:**
    - Coverage status (true/false)
    - Alternative data sources for out-of-coverage areas
    - Regional information
    """
    try:
        # Check TEMPO coverage using the enhanced connector
        async with enhanced_service.connector as conn:
            tempo_coverage = conn.is_in_tempo_coverage(latitude, longitude)
        
        coverage_info = {
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'tempo_coverage': tempo_coverage,
            'coverage_area': {
                'lat_min': 15.0,
                'lat_max': 70.0,
                'lon_min': -140.0,
                'lon_max': -40.0,
                'description': 'North America geostationary coverage'
            },
            'alternative_sources': [
                'OpenAQ Global Network',
                'Sentinel-5P Satellite (Global)',
                'Ground Station Networks',
                'Regional Air Quality Agencies'
            ] if not tempo_coverage else [],
            'data_availability': 'ENHANCED' if tempo_coverage else 'STANDARD',
            'update_frequency': 'Hourly (daylight)' if tempo_coverage else 'Varies by source'
        }
        
        return coverage_info
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking TEMPO coverage: {str(e)}"
        )

@router.get("/location/who-analysis")
async def get_who_compliance_analysis(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees")
):
    """
    Get detailed WHO air quality guidelines compliance analysis.
    
    **WHO Guidelines (2021 Update):**
    - PM2.5: Annual 5 µg/m³, 24h 15 µg/m³
    - PM10: Annual 15 µg/m³, 24h 45 µg/m³  
    - NO2: Annual 10 µg/m³, 24h 25 µg/m³
    - O3: 8h 100 µg/m³
    - SO2: 24h 40 µg/m³
    
    **Returns:**
    - Current pollutant levels vs WHO guidelines
    - Exceedance factors and health risks
    - Population health impact estimates
    - Recommendations for sensitive groups
    """
    try:
        # Get comprehensive data first
        data = await enhanced_service.get_complete_location_data(latitude, longitude)
        
        # Extract WHO-specific analysis
        who_analysis = {
            'location': data['location'],
            'timestamp': data['timestamp'],
            'who_guidelines_2021': enhanced_service.who_guidelines,
            'compliance_status': data.get('who_compliance', {}),
            'pollutant_analysis': {},
            'health_recommendations': data.get('health_recommendations', []),
            'risk_assessment': {
                'overall_risk': 'UNKNOWN',
                'sensitive_groups_risk': 'UNKNOWN',
                'population_exposure': 'UNKNOWN'
            }
        }
        
        # Detailed pollutant analysis
        for pollutant, pollutant_data in data.get('pollutants', {}).items():
            if pollutant in enhanced_service.who_guidelines:
                who_analysis['pollutant_analysis'][pollutant] = {
                    'current_value': pollutant_data['value'],
                    'unit': pollutant_data['unit'],
                    'who_guideline': pollutant_data['who_guideline'],
                    'exceeds_who': pollutant_data['exceeds_who'],
                    'compliance_details': data['who_compliance'].get(pollutant, {}),
                    'health_impact': enhanced_service._get_health_impact_description(pollutant)
                }
        
        # Calculate overall risk assessment
        exceedances = sum(1 for p in who_analysis['pollutant_analysis'].values() if p['exceeds_who'])
        total_pollutants = len(who_analysis['pollutant_analysis'])
        
        if exceedances == 0:
            who_analysis['risk_assessment']['overall_risk'] = 'LOW'
            who_analysis['risk_assessment']['sensitive_groups_risk'] = 'LOW'
        elif exceedances <= total_pollutants / 2:
            who_analysis['risk_assessment']['overall_risk'] = 'MODERATE'
            who_analysis['risk_assessment']['sensitive_groups_risk'] = 'MODERATE_TO_HIGH'
        else:
            who_analysis['risk_assessment']['overall_risk'] = 'HIGH'
            who_analysis['risk_assessment']['sensitive_groups_risk'] = 'HIGH'
        
        return who_analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating WHO analysis: {str(e)}"
        )

@router.get("/location/data-sources")
async def get_available_data_sources(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude in decimal degrees")
):
    """
    Get information about available data sources for a specific location.
    
    **Global Data Sources:**
    - NASA TEMPO (North America only)
    - OpenAQ Global Network
    - NASA Ground Stations
    - International Space Agencies
    - Regional Air Quality Networks
    
    **Returns:**
    - Available sources for the location
    - Data quality and update frequency
    - Coverage limitations
    - Recommended primary sources
    """
    try:
        # Determine available sources based on location
        region = enhanced_service._get_region(latitude, longitude)
        tempo_coverage = enhanced_service.connector.is_in_tempo_coverage(latitude, longitude)
        
        sources_info = {
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'region': region
            },
            'primary_sources': [],
            'secondary_sources': [],
            'data_quality_assessment': {},
            'update_frequencies': {},
            'coverage_notes': []
        }
        
        # NASA TEMPO
        if tempo_coverage:
            sources_info['primary_sources'].append({
                'name': 'NASA TEMPO Satellite',
                'type': 'Satellite',
                'pollutants': ['NO2', 'O3', 'HCHO', 'Aerosol Index'],
                'coverage': 'North America',
                'update_frequency': 'Hourly (daylight)',
                'quality': 'EXCELLENT',
                'spatial_resolution': '2.1 km × 4.4 km'
            })
        
        # OpenAQ Global Network
        sources_info['primary_sources'].append({
            'name': 'OpenAQ Global Network',
            'type': 'Ground Stations',
            'pollutants': ['PM2.5', 'PM10', 'NO2', 'O3', 'SO2', 'CO'],
            'coverage': 'Global (150+ countries)',
            'update_frequency': 'Real-time to hourly',
            'quality': 'GOOD',
            'station_density': 'Varies by region'
        })
        
        # Regional sources based on location
        if region == 'North America':
            sources_info['secondary_sources'].extend([
                {
                    'name': 'AirNow (EPA)',
                    'type': 'Government Network',
                    'coverage': 'USA/Canada',
                    'quality': 'EXCELLENT'
                },
                {
                    'name': 'NASA Pandora Network',
                    'type': 'Ground-based Spectrometry',
                    'coverage': 'Selected cities',
                    'quality': 'EXCELLENT'
                }
            ])
        elif region == 'Europe':
            sources_info['secondary_sources'].append({
                'name': 'European Environment Agency',
                'type': 'Government Network',
                'coverage': 'EU Countries',
                'quality': 'EXCELLENT'
            })
        elif region == 'South America':
            sources_info['secondary_sources'].extend([
                {
                    'name': 'Brazilian SEEG',
                    'type': 'Emissions Database',
                    'coverage': 'Brazil',
                    'quality': 'GOOD'
                },
                {
                    'name': 'CPTEC/INPE',
                    'type': 'Weather/Climate',
                    'coverage': 'South America',
                    'quality': 'GOOD'
                }
            ])
        
        # Add international satellite sources
        sources_info['secondary_sources'].append({
            'name': 'Sentinel-5P TROPOMI',
            'type': 'Satellite',
            'pollutants': ['NO2', 'O3', 'CO', 'CH4', 'SO2'],
            'coverage': 'Global',
            'update_frequency': 'Daily',
            'quality': 'GOOD',
            'spatial_resolution': '7 km × 3.5 km'
        })
        
        return sources_info
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting data sources info: {str(e)}"
        )

# Add helper method to enhanced service
def _get_health_impact_description(self, pollutant: str) -> str:
    """Get health impact description for pollutant"""
    health_impacts = {
        'pm25': 'Cardiovascular disease, respiratory illness, lung cancer, premature death',
        'pm10': 'Respiratory symptoms, reduced lung function, aggravated asthma',
        'no2': 'Respiratory symptoms, reduced lung function, increased respiratory infections',
        'o3': 'Respiratory symptoms, reduced lung function, aggravated asthma, premature death',
        'so2': 'Respiratory symptoms, hospital admissions, aggravated asthma',
        'co': 'Cardiovascular effects, reduced oxygen delivery to organs'
    }
    return health_impacts.get(pollutant, 'Various health effects possible')

# Monkey patch the method
EnhancedNASATempoService._get_health_impact_description = _get_health_impact_description
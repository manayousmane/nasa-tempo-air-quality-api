"""
Configuration for real API connections
"""
import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class APIConfig:
    """Configuration for external APIs"""
    
    # NASA Earthdata credentials
    nasa_username: Optional[str] = None
    nasa_password: Optional[str] = None
    nasa_token: Optional[str] = None
    
    # OpenAQ API
    openaq_api_key: Optional[str] = None
    
    # AQICN API
    aqicn_api_key: Optional[str] = None
    
    # EPA AirNow API
    epa_api_key: Optional[str] = None
    
    # OpenWeatherMap API
    openweather_api_key: Optional[str] = None

def load_config() -> APIConfig:
    """Load configuration from environment variables"""
    return APIConfig(
        nasa_username=os.getenv('NASA_EARTHDATA_USERNAME'),
        nasa_password=os.getenv('NASA_EARTHDATA_PASSWORD'),
        nasa_token=os.getenv('NASA_EARTHDATA_TOKEN'),
        openaq_api_key=os.getenv('OPENAQ_API_KEY'),
        aqicn_api_key=os.getenv('AQICN_API_KEY'),
        epa_api_key=os.getenv('EPA_API_KEY'),
        openweather_api_key=os.getenv('OPENWEATHER_API_KEY')
    )

# API URLs
API_URLS = {
    'nasa_earthdata_token': 'https://urs.earthdata.nasa.gov/api/users/token',
    'nasa_tempo_data': 'https://earthdata.nasa.gov/api/tempo/data',
    'openaq_base': 'https://api.openaq.org/v3',  # Updated to v3
    'aqicn_base': 'https://api.waqi.info',
    'epa_airnow': 'https://www.airnowapi.org/aq',
    'sentinel5p_base': 'https://catalogue.dataspace.copernicus.eu/stac'
}
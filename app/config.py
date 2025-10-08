# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # NASA
    NASA_USERNAME = os.getenv('NASA_EARTHDATA_USERNAME')
    NASA_PASSWORD = os.getenv('NASA_EARTHDATA_PASSWORD')
    TEMPO_BASE_URL = os.getenv('TEMPO_API_BASE_URL')
    
    # OpenAQ
    OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')
    OPENAQ_BASE_URL = os.getenv('OPENAQ_API_BASE_URL')
    
    # Weather
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    OPENWEATHER_BASE_URL = os.getenv('OPENWEATHER_API_BASE_URL')
    
    # App Config
    APP_ENV = os.getenv('APP_ENV', 'development')
    CACHE_TTL = int(os.getenv('CACHE_TTL', 600))
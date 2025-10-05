"""
Ground-based air quality data collection service.
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GroundDataCollector:
    """Collector for ground-based air quality measurements."""
    
    def __init__(self):
        self.epa_api_key = settings.EPA_API_KEY
        self.openaq_api_key = settings.OPENAQ_API_KEY
        self.pandora_api_url = settings.PANDORA_API_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_epa_data(self, latitude: float, longitude: float, radius_km: float = 25) -> List[Dict[str, Any]]:
        """
        Get EPA AirNow data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers
        
        Returns:
            List of EPA air quality measurements
        """
        if not self.session or not self.epa_api_key:
            logger.warning("EPA API not configured")
            return []
        
        try:
            # EPA AirNow API endpoint
            url = "https://www.airnowapi.org/aq/observation/latLong/current/"
            params = {
                "format": "application/json",
                "latitude": latitude,
                "longitude": longitude,
                "distance": radius_km,
                "API_KEY": self.epa_api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_epa_data(data)
                else:
                    logger.error(f"EPA API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching EPA data: {e}")
            return []
    
    async def get_openaq_data(self, latitude: float, longitude: float, radius_km: float = 25) -> List[Dict[str, Any]]:
        """
        Get OpenAQ data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers
        
        Returns:
            List of OpenAQ air quality measurements
        """
        if not self.session:
            logger.warning("Session not initialized")
            return []
        
        try:
            # OpenAQ API v2 endpoint
            url = "https://api.openaq.org/v2/latest"
            params = {
                "coordinates": f"{latitude},{longitude}",
                "radius": radius_km * 1000,  # Convert to meters
                "limit": 100,
                "order_by": "lastUpdated",
                "sort": "desc"
            }
            
            headers = {}
            if self.openaq_api_key:
                headers["X-API-Key"] = self.openaq_api_key
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_openaq_data(data)
                else:
                    logger.error(f"OpenAQ API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching OpenAQ data: {e}")
            return []
    
    async def get_pandora_data(self, latitude: float, longitude: float, radius_km: float = 50) -> List[Dict[str, Any]]:
        """
        Get Pandora network data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            radius_km: Search radius in kilometers
        
        Returns:
            List of Pandora measurements
        """
        if not self.session:
            logger.warning("Session not initialized")
            return []
        
        try:
            # Pandora API endpoint for latest data
            url = f"{self.pandora_api_url}/latest"
            params = {
                "lat": latitude,
                "lon": longitude,
                "radius": radius_km,
                "format": "json"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_pandora_data(data)
                else:
                    logger.error(f"Pandora API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching Pandora data: {e}")
            return []
    
    async def get_all_ground_data(self, latitude: float, longitude: float) -> List[Dict[str, Any]]:
        """
        Get data from all available ground sources.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            Combined list of ground-based measurements
        """
        all_data = []
        
        # Collect data from all sources in parallel
        tasks = []
        
        if self.epa_api_key:
            tasks.append(self.get_epa_data(latitude, longitude))
        
        tasks.append(self.get_openaq_data(latitude, longitude))
        tasks.append(self.get_pandora_data(latitude, longitude))
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list) and not isinstance(result, Exception):
                    all_data.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error in ground data collection: {result}")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error collecting ground data: {e}")
            return []
    
    def _process_epa_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process EPA AirNow data."""
        processed_data = []
        
        try:
            for item in data:
                processed = {
                    "source": "EPA",
                    "timestamp": datetime.fromisoformat(item.get("DateObserved", "") + "T" + item.get("HourObserved", "00") + ":00:00"),
                    "quality_flag": "good",
                    "confidence": 0.9
                }
                
                # Map EPA parameters
                parameter = item.get("ParameterName", "").upper()
                value = item.get("AQI")
                
                if parameter == "PM2.5" and value is not None:
                    processed["pm25"] = float(value)
                elif parameter == "PM10" and value is not None:
                    processed["pm10"] = float(value)
                elif parameter == "OZONE" and value is not None:
                    processed["o3"] = float(value)
                elif parameter == "NO2" and value is not None:
                    processed["no2"] = float(value)
                
                # EPA provides AQI directly
                if "AQI" in item and item["AQI"] is not None:
                    processed["aqi"] = int(item["AQI"])
                    processed["aqi_category"] = item.get("Category", {}).get("Name", "")
                
                processed_data.append(processed)
                
        except Exception as e:
            logger.error(f"Error processing EPA data: {e}")
        
        return processed_data
    
    def _process_openaq_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process OpenAQ data."""
        processed_data = []
        
        try:
            results = data.get("results", [])
            
            for item in results:
                measurements = item.get("measurements", [])
                
                for measurement in measurements:
                    processed = {
                        "source": "OpenAQ",
                        "timestamp": datetime.fromisoformat(measurement.get("lastUpdated", "").replace("Z", "+00:00")),
                        "quality_flag": "good",
                        "confidence": 0.8
                    }
                    
                    # Map OpenAQ parameters
                    parameter = measurement.get("parameter", "").lower()
                    value = measurement.get("value")
                    unit = measurement.get("unit", "")
                    
                    if parameter == "pm25" and value is not None:
                        processed["pm25"] = float(value)
                    elif parameter == "pm10" and value is not None:
                        processed["pm10"] = float(value)
                    elif parameter == "o3" and value is not None:
                        processed["o3"] = float(value)
                    elif parameter == "no2" and value is not None:
                        processed["no2"] = float(value)
                    elif parameter == "co" and value is not None:
                        processed["co"] = float(value)
                    elif parameter == "so2" and value is not None:
                        processed["so2"] = float(value)
                    
                    processed_data.append(processed)
                    
        except Exception as e:
            logger.error(f"Error processing OpenAQ data: {e}")
        
        return processed_data
    
    def _process_pandora_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Pandora network data."""
        processed_data = []
        
        try:
            stations = data.get("stations", [])
            
            for station in stations:
                measurements = station.get("measurements", [])
                
                for measurement in measurements:
                    processed = {
                        "source": "Pandora",
                        "timestamp": datetime.fromisoformat(measurement.get("timestamp", "")),
                        "quality_flag": measurement.get("quality_flag", "good"),
                        "confidence": 0.85
                    }
                    
                    # Pandora specializes in trace gases
                    if "no2" in measurement:
                        processed["no2"] = float(measurement["no2"])
                    if "o3" in measurement:
                        processed["o3"] = float(measurement["o3"])
                    if "hcho" in measurement:
                        processed["hcho"] = float(measurement["hcho"])
                    
                    processed_data.append(processed)
                    
        except Exception as e:
            logger.error(f"Error processing Pandora data: {e}")
        
        return processed_data


# Global collector instance
ground_collector = GroundDataCollector()
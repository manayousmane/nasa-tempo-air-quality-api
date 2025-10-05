"""
NASA TEMPO satellite data collection service.
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class TempoDataCollector:
    """Collector for NASA TEMPO satellite data."""
    
    def __init__(self):
        self.base_url = settings.TEMPO_DATA_URL
        self.username = settings.NASA_EARTHDATA_USERNAME
        self.password = settings.NASA_EARTHDATA_PASSWORD
        self.token = settings.NASA_EARTHDATA_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate with NASA Earthdata API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            auth_url = f"{self.base_url}/auth/token"
            
            if self.token:
                # Use existing token
                headers = {"Authorization": f"Bearer {self.token}"}
                async with self.session.get(f"{self.base_url}/validate", headers=headers) as response:
                    return response.status == 200
            
            elif self.username and self.password:
                # Get new token
                auth_data = {
                    "username": self.username,
                    "password": self.password
                }
                async with self.session.post(auth_url, json=auth_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.token = data.get("access_token")
                        return True
                    
            logger.error("Authentication failed - no valid credentials")
            return False
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def get_latest_data(self, 
                            latitude: float, 
                            longitude: float,
                            parameters: List[str] = None) -> Dict[str, Any]:
        """
        Get latest TEMPO data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            parameters: List of parameters to retrieve (NO2, O3, HCHO, etc.)
        
        Returns:
            Dictionary containing latest measurements
        """
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        if parameters is None:
            parameters = ["NO2", "O3", "HCHO", "AEROSOL"]
        
        try:
            # Build query parameters
            query_params = {
                "lat": latitude,
                "lon": longitude,
                "parameters": ",".join(parameters),
                "format": "json",
                "latest": "true"
            }
            
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            async with self.session.get(
                f"{self.base_url}/data/latest",
                params=query_params,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return await self._process_tempo_data(data)
                elif response.status == 401:
                    logger.warning("Token expired, re-authenticating...")
                    if await self.authenticate():
                        return await self.get_latest_data(latitude, longitude, parameters)
                    else:
                        raise Exception("Authentication failed")
                else:
                    logger.error(f"API request failed: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error fetching TEMPO data: {e}")
            return {}
    
    async def get_historical_data(self,
                                latitude: float,
                                longitude: float,
                                start_date: datetime,
                                end_date: datetime,
                                parameters: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get historical TEMPO data for a location and time range.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start of time range
            end_date: End of time range
            parameters: List of parameters to retrieve
        
        Returns:
            List of measurement dictionaries
        """
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        if parameters is None:
            parameters = ["NO2", "O3", "HCHO", "AEROSOL"]
        
        try:
            query_params = {
                "lat": latitude,
                "lon": longitude,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "parameters": ",".join(parameters),
                "format": "json"
            }
            
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            
            async with self.session.get(
                f"{self.base_url}/data/historical",
                params=query_params,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return await self._process_historical_data(data)
                else:
                    logger.error(f"Historical data request failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching historical TEMPO data: {e}")
            return []
    
    async def _process_tempo_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw TEMPO data into standardized format."""
        try:
            processed = {
                "source": "TEMPO",
                "timestamp": datetime.fromisoformat(raw_data.get("timestamp", datetime.utcnow().isoformat())),
                "quality_flag": raw_data.get("quality_flag", "good"),
                "confidence": raw_data.get("confidence", 0.8)
            }
            
            # Map TEMPO parameters to our schema
            parameter_mapping = {
                "NO2": "no2",
                "O3": "o3", 
                "HCHO": "hcho",
                "AEROSOL_PM25": "pm25"
            }
            
            measurements = raw_data.get("measurements", {})
            for tempo_param, our_param in parameter_mapping.items():
                if tempo_param in measurements:
                    value = measurements[tempo_param].get("value")
                    if value is not None:
                        processed[our_param] = float(value)
            
            # Calculate AQI if we have enough data
            if any(param in processed for param in ["pm25", "no2", "o3"]):
                processed["aqi"] = self._calculate_aqi(processed)
                processed["aqi_category"] = self._get_aqi_category(processed["aqi"])
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing TEMPO data: {e}")
            return {}
    
    async def _process_historical_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process historical TEMPO data."""
        try:
            processed_data = []
            records = raw_data.get("records", [])
            
            for record in records:
                processed = await self._process_tempo_data(record)
                if processed:
                    processed_data.append(processed)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing historical TEMPO data: {e}")
            return []
    
    def _calculate_aqi(self, data: Dict[str, Any]) -> int:
        """Calculate Air Quality Index from pollutant concentrations."""
        # Simplified AQI calculation - in production, use EPA's official formula
        try:
            aqi_values = []
            
            # PM2.5 AQI calculation (μg/m³)
            if "pm25" in data:
                pm25 = data["pm25"]
                if pm25 <= 12.0:
                    aqi_pm25 = (50 / 12.0) * pm25
                elif pm25 <= 35.4:
                    aqi_pm25 = 50 + ((100 - 50) / (35.4 - 12.1)) * (pm25 - 12.1)
                elif pm25 <= 55.4:
                    aqi_pm25 = 100 + ((150 - 100) / (55.4 - 35.5)) * (pm25 - 35.5)
                else:
                    aqi_pm25 = min(500, 150 + ((500 - 150) / (500 - 55.5)) * (pm25 - 55.5))
                aqi_values.append(aqi_pm25)
            
            # NO2 AQI calculation (ppb)
            if "no2" in data:
                no2 = data["no2"]
                if no2 <= 53:
                    aqi_no2 = (50 / 53) * no2
                elif no2 <= 100:
                    aqi_no2 = 50 + ((100 - 50) / (100 - 54)) * (no2 - 54)
                else:
                    aqi_no2 = min(500, 100 + ((500 - 100) / (2000 - 101)) * (no2 - 101))
                aqi_values.append(aqi_no2)
            
            # O3 AQI calculation (ppb)
            if "o3" in data:
                o3 = data["o3"]
                if o3 <= 54:
                    aqi_o3 = (50 / 54) * o3
                elif o3 <= 70:
                    aqi_o3 = 50 + ((100 - 50) / (70 - 55)) * (o3 - 55)
                else:
                    aqi_o3 = min(500, 100 + ((500 - 100) / (405 - 71)) * (o3 - 71))
                aqi_values.append(aqi_o3)
            
            return int(max(aqi_values)) if aqi_values else 0
            
        except Exception as e:
            logger.error(f"Error calculating AQI: {e}")
            return 0
    
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


# Global collector instance
tempo_collector = TempoDataCollector()
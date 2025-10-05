"""
Weather data collection service.
"""
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WeatherDataCollector:
    """Collector for weather data from various APIs."""
    
    def __init__(self):
        self.openweather_api_key = settings.OPENWEATHER_API_KEY
        self.noaa_token = settings.NOAA_API_TOKEN
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get current weather data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
        
        Returns:
            Dictionary containing current weather data
        """
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            # Try OpenWeatherMap first
            if self.openweather_api_key:
                weather_data = await self._get_openweather_current(latitude, longitude)
                if weather_data:
                    return weather_data
            
            # Fallback to NOAA if available
            if self.noaa_token:
                weather_data = await self._get_noaa_current(latitude, longitude)
                if weather_data:
                    return weather_data
            
            logger.warning("No weather data sources available")
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return {}
    
    async def get_weather_forecast(self, 
                                 latitude: float, 
                                 longitude: float,
                                 hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get weather forecast for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            hours: Number of hours to forecast
        
        Returns:
            List of weather forecast data
        """
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            # Try OpenWeatherMap first
            if self.openweather_api_key:
                forecast_data = await self._get_openweather_forecast(latitude, longitude, hours)
                if forecast_data:
                    return forecast_data
            
            # Fallback to NOAA
            if self.noaa_token:
                forecast_data = await self._get_noaa_forecast(latitude, longitude, hours)
                if forecast_data:
                    return forecast_data
            
            logger.warning("No weather forecast sources available")
            return []
            
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return []
    
    async def _get_openweather_current(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current weather from OpenWeatherMap API."""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_openweather_current(data)
                else:
                    logger.error(f"OpenWeatherMap API error: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error fetching OpenWeatherMap current data: {e}")
            return {}
    
    async def _get_openweather_forecast(self, 
                                      latitude: float, 
                                      longitude: float, 
                                      hours: int) -> List[Dict[str, Any]]:
        """Get weather forecast from OpenWeatherMap API."""
        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_openweather_forecast(data, hours)
                else:
                    logger.error(f"OpenWeatherMap forecast API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching OpenWeatherMap forecast: {e}")
            return []
    
    async def _get_noaa_current(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current weather from NOAA API."""
        try:
            # NOAA API endpoint for current conditions
            # Note: This is a simplified implementation
            url = f"https://api.weather.gov/points/{latitude},{longitude}"
            headers = {"User-Agent": "NASA-TEMPO-App/1.0"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Get the observation station URL
                    properties = data.get("properties", {})
                    forecast_office = properties.get("forecastOffice")
                    grid_x = properties.get("gridX")
                    grid_y = properties.get("gridY")
                    
                    if forecast_office and grid_x and grid_y:
                        # Get current conditions
                        obs_url = f"https://api.weather.gov/gridpoints/{forecast_office}/{grid_x},{grid_y}/forecast"
                        async with self.session.get(obs_url, headers=headers) as obs_response:
                            if obs_response.status == 200:
                                obs_data = await obs_response.json()
                                return self._process_noaa_current(obs_data)
                    
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching NOAA current data: {e}")
            return {}
    
    async def _get_noaa_forecast(self, 
                               latitude: float, 
                               longitude: float, 
                               hours: int) -> List[Dict[str, Any]]:
        """Get weather forecast from NOAA API."""
        try:
            # Similar to current weather but get forecast data
            url = f"https://api.weather.gov/points/{latitude},{longitude}"
            headers = {"User-Agent": "NASA-TEMPO-App/1.0"}
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    properties = data.get("properties", {})
                    forecast_url = properties.get("forecast")
                    
                    if forecast_url:
                        async with self.session.get(forecast_url, headers=headers) as forecast_response:
                            if forecast_response.status == 200:
                                forecast_data = await forecast_response.json()
                                return self._process_noaa_forecast(forecast_data, hours)
                    
                return []
                
        except Exception as e:
            logger.error(f"Error fetching NOAA forecast: {e}")
            return []
    
    def _process_openweather_current(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpenWeatherMap current weather data."""
        try:
            main = data.get("main", {})
            wind = data.get("wind", {})
            weather = data.get("weather", [{}])[0]
            clouds = data.get("clouds", {})
            
            processed = {
                "source": "OpenWeather",
                "timestamp": datetime.utcnow(),
                "temperature": main.get("temp"),
                "humidity": main.get("humidity"),
                "pressure": main.get("pressure"),
                "wind_speed": wind.get("speed"),
                "wind_direction": wind.get("deg"),
                "cloud_cover": clouds.get("all"),
                "visibility": data.get("visibility", 0) / 1000 if data.get("visibility") else None,  # Convert to km
                "condition": weather.get("main"),
                "description": weather.get("description")
            }
            
            # Add precipitation if available
            if "rain" in data:
                processed["precipitation"] = data["rain"].get("1h", 0)
            elif "snow" in data:
                processed["precipitation"] = data["snow"].get("1h", 0)
            else:
                processed["precipitation"] = 0
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap current data: {e}")
            return {}
    
    def _process_openweather_forecast(self, data: Dict[str, Any], hours: int) -> List[Dict[str, Any]]:
        """Process OpenWeatherMap forecast data."""
        try:
            processed_data = []
            forecast_list = data.get("list", [])
            
            # Limit to requested hours (each forecast point is 3 hours)
            max_points = min(len(forecast_list), hours // 3 + 1)
            
            for i in range(max_points):
                item = forecast_list[i]
                main = item.get("main", {})
                wind = item.get("wind", {})
                weather = item.get("weather", [{}])[0]
                clouds = item.get("clouds", {})
                
                processed = {
                    "source": "OpenWeather",
                    "timestamp": datetime.fromtimestamp(item.get("dt", 0)),
                    "temperature": main.get("temp"),
                    "humidity": main.get("humidity"),
                    "pressure": main.get("pressure"),
                    "wind_speed": wind.get("speed"),
                    "wind_direction": wind.get("deg"),
                    "cloud_cover": clouds.get("all"),
                    "condition": weather.get("main"),
                    "description": weather.get("description"),
                    "precipitation": item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0)
                }
                
                processed_data.append(processed)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing OpenWeatherMap forecast: {e}")
            return []
    
    def _process_noaa_current(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process NOAA current weather data."""
        try:
            # NOAA data structure is different - simplified processing
            properties = data.get("properties", {})
            periods = properties.get("periods", [])
            
            if not periods:
                return {}
            
            current = periods[0]
            
            processed = {
                "source": "NOAA",
                "timestamp": datetime.utcnow(),
                "temperature": current.get("temperature"),
                "condition": current.get("shortForecast"),
                "description": current.get("detailedForecast"),
                "wind_speed": self._parse_wind_speed(current.get("windSpeed", "")),
                "wind_direction": current.get("windDirection")
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing NOAA current data: {e}")
            return {}
    
    def _process_noaa_forecast(self, data: Dict[str, Any], hours: int) -> List[Dict[str, Any]]:
        """Process NOAA forecast data."""
        try:
            processed_data = []
            properties = data.get("properties", {})
            periods = properties.get("periods", [])
            
            # Limit to requested time range
            max_periods = min(len(periods), hours // 12 + 1)  # NOAA typically gives 12-hour periods
            
            for i in range(max_periods):
                period = periods[i]
                
                processed = {
                    "source": "NOAA",
                    "timestamp": datetime.fromisoformat(period.get("startTime", "").replace("Z", "+00:00")),
                    "temperature": period.get("temperature"),
                    "condition": period.get("shortForecast"),
                    "description": period.get("detailedForecast"),
                    "wind_speed": self._parse_wind_speed(period.get("windSpeed", "")),
                    "wind_direction": period.get("windDirection")
                }
                
                processed_data.append(processed)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing NOAA forecast: {e}")
            return []
    
    def _parse_wind_speed(self, wind_str: str) -> Optional[float]:
        """Parse wind speed from NOAA string format."""
        try:
            if not wind_str:
                return None
            
            # Extract numeric part (e.g., "10 mph" -> 10)
            import re
            match = re.search(r"(\d+)", wind_str)
            if match:
                speed_mph = float(match.group(1))
                # Convert mph to m/s
                return speed_mph * 0.44704
            
            return None
            
        except Exception:
            return None


# Global collector instance
weather_collector = WeatherDataCollector()
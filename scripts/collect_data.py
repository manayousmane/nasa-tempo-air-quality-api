"""
Data collection script for gathering air quality data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List

from app.data import tempo_collector, weather_collector, ground_collector
from app.core.logging import get_logger

logger = get_logger(__name__)


async def collect_data_for_locations(locations: List[dict]):
    """
    Collect data for specified locations.
    
    Args:
        locations: List of location dictionaries with lat, lon, name
    """
    try:
        logger.info(f"Starting data collection for {len(locations)} locations")
        
        for location in locations:
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["name"]
            
            logger.info(f"Collecting data for {name}")
            
            # Collect data from all sources
            tasks = [
                collect_tempo_data(lat, lon, name),
                collect_weather_data(lat, lon, name),
                collect_ground_data(lat, lon, name)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            for i, result in enumerate(results):
                source = ["TEMPO", "Weather", "Ground"][i]
                if isinstance(result, Exception):
                    logger.error(f"Error collecting {source} data for {name}: {result}")
                else:
                    logger.info(f"Successfully collected {source} data for {name}")
            
            # Small delay between locations
            await asyncio.sleep(1)
        
        logger.info("Data collection completed")
        
    except Exception as e:
        logger.error(f"Error in data collection: {e}")


async def collect_tempo_data(latitude: float, longitude: float, location_name: str):
    """Collect TEMPO satellite data."""
    try:
        async with tempo_collector as collector:
            if await collector.authenticate():
                data = await collector.get_latest_data(latitude, longitude)
                if data:
                    logger.info(f"TEMPO data collected for {location_name}: {len(data)} parameters")
                    return data
                else:
                    logger.warning(f"No TEMPO data available for {location_name}")
            else:
                logger.error(f"Failed to authenticate with TEMPO API for {location_name}")
        return {}
    except Exception as e:
        logger.error(f"Error collecting TEMPO data for {location_name}: {e}")
        return {}


async def collect_weather_data(latitude: float, longitude: float, location_name: str):
    """Collect weather data."""
    try:
        async with weather_collector as collector:
            data = await collector.get_current_weather(latitude, longitude)
            if data:
                logger.info(f"Weather data collected for {location_name}")
                return data
            else:
                logger.warning(f"No weather data available for {location_name}")
        return {}
    except Exception as e:
        logger.error(f"Error collecting weather data for {location_name}: {e}")
        return {}


async def collect_ground_data(latitude: float, longitude: float, location_name: str):
    """Collect ground-based air quality data."""
    try:
        async with ground_collector as collector:
            data = await collector.get_all_ground_data(latitude, longitude)
            if data:
                logger.info(f"Ground data collected for {location_name}: {len(data)} measurements")
                return data
            else:
                logger.warning(f"No ground data available for {location_name}")
        return []
    except Exception as e:
        logger.error(f"Error collecting ground data for {location_name}: {e}")
        return []


async def main():
    """Main data collection routine."""
    # Sample locations for data collection
    locations = [
        {"name": "Los Angeles, CA", "latitude": 34.0522, "longitude": -118.2437},
        {"name": "New York, NY", "latitude": 40.7128, "longitude": -74.0060},
        {"name": "Houston, TX", "latitude": 29.7604, "longitude": -95.3698},
        {"name": "Chicago, IL", "latitude": 41.8781, "longitude": -87.6298},
        {"name": "Denver, CO", "latitude": 39.7392, "longitude": -104.9903}
    ]
    
    await collect_data_for_locations(locations)


if __name__ == "__main__":
    asyncio.run(main())
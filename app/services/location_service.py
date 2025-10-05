"""
Location service for managing monitoring locations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.schemas import Location, LocationCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


class LocationService:
    """Service for location operations."""
    
    def __init__(self):
        # In a real implementation, this would use a database
        self._sample_locations = self._get_sample_locations()
    
    async def get_locations(self,
                          country: Optional[str] = None,
                          state: Optional[str] = None,
                          active_only: bool = True,
                          limit: int = 100) -> List[Location]:
        """
        Get list of monitoring locations.
        
        Args:
            country: Filter by country
            state: Filter by state
            active_only: Only active locations
            limit: Maximum number of locations
        
        Returns:
            List of locations
        """
        try:
            locations = self._sample_locations.copy()
            
            # Apply filters
            if country:
                locations = [l for l in locations if l.country.lower() == country.lower()]
            
            if state:
                locations = [l for l in locations if l.state and l.state.lower() == state.lower()]
            
            if active_only:
                locations = [l for l in locations if l.is_active]
            
            # Apply limit
            return locations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting locations: {e}")
            return []
    
    async def get_location(self, location_id: int) -> Optional[Location]:
        """
        Get a specific location by ID.
        
        Args:
            location_id: Location identifier
        
        Returns:
            Location object or None if not found
        """
        try:
            for location in self._sample_locations:
                if location.id == location_id:
                    return location
            return None
            
        except Exception as e:
            logger.error(f"Error getting location {location_id}: {e}")
            return None
    
    async def find_nearby_locations(self,
                                  latitude: float,
                                  longitude: float,
                                  radius_km: float = 50,
                                  limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find locations near a point.
        
        Args:
            latitude: Search center latitude
            longitude: Search center longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of locations
        
        Returns:
            List of nearby locations with distance
        """
        try:
            nearby_locations = []
            
            for location in self._sample_locations:
                if not location.is_active:
                    continue
                
                # Calculate distance using Haversine formula
                distance_km = self._calculate_distance(
                    latitude, longitude,
                    location.latitude, location.longitude
                )
                
                if distance_km <= radius_km:
                    nearby_locations.append({
                        "location": location,
                        "distance_km": round(distance_km, 2)
                    })
            
            # Sort by distance
            nearby_locations.sort(key=lambda x: x["distance_km"])
            
            return nearby_locations[:limit]
            
        except Exception as e:
            logger.error(f"Error finding nearby locations: {e}")
            return []
    
    async def create_location(self, location_data: LocationCreate) -> Location:
        """
        Create a new monitoring location.
        
        Args:
            location_data: Location creation data
        
        Returns:
            Created location
        """
        try:
            # Generate new ID
            max_id = max([l.id for l in self._sample_locations]) if self._sample_locations else 0
            new_id = max_id + 1
            
            # Create new location
            new_location = Location(
                id=new_id,
                name=location_data.name,
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                country=location_data.country,
                state=location_data.state,
                city=location_data.city,
                postal_code=location_data.postal_code,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            # Add to sample locations (in real app, save to database)
            self._sample_locations.append(new_location)
            
            logger.info(f"Created new location: {new_location.name}")
            return new_location
            
        except Exception as e:
            logger.error(f"Error creating location: {e}")
            raise
    
    async def get_global_coverage(self) -> Dict[str, Any]:
        """
        Get global coverage statistics.
        
        Returns:
            Coverage statistics and information
        """
        try:
            # Analyze current locations
            countries = set(l.country for l in self._sample_locations if l.is_active)
            states = set(l.state for l in self._sample_locations if l.is_active and l.state)
            
            # Count by region
            region_counts = {}
            for location in self._sample_locations:
                if location.is_active:
                    region = self._get_region(location.country)
                    region_counts[region] = region_counts.get(region, 0) + 1
            
            # Data source availability
            data_sources = {
                "TEMPO": {"coverage": "North America", "locations": len(self._sample_locations)},
                "EPA": {"coverage": "United States", "locations": len([l for l in self._sample_locations if l.country == "United States"])},
                "OpenAQ": {"coverage": "Global", "locations": len(self._sample_locations)},
                "Pandora": {"coverage": "Global Network", "locations": 15}  # Sample number
            }
            
            return {
                "total_locations": len([l for l in self._sample_locations if l.is_active]),
                "countries_covered": len(countries),
                "states_covered": len(states),
                "region_distribution": region_counts,
                "data_source_coverage": data_sources,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global coverage: {e}")
            return {}
    
    async def get_location_data_sources(self, location_id: int) -> List[Dict[str, Any]]:
        """
        Get available data sources for a location.
        
        Args:
            location_id: Location identifier
        
        Returns:
            List of available data sources
        """
        try:
            location = await self.get_location(location_id)
            if not location:
                return []
            
            # Determine available data sources based on location
            data_sources = []
            
            # TEMPO coverage (North America)
            if location.country in ["United States", "Canada", "Mexico"]:
                data_sources.append({
                    "name": "TEMPO",
                    "type": "satellite",
                    "parameters": ["NO2", "O3", "HCHO", "Aerosols"],
                    "update_frequency": "hourly",
                    "spatial_resolution": "2.1 x 4.4 km",
                    "reliability": 0.85,
                    "status": "active"
                })
            
            # EPA AirNow (United States)
            if location.country == "United States":
                data_sources.append({
                    "name": "EPA AirNow",
                    "type": "ground_station",
                    "parameters": ["PM2.5", "PM10", "O3", "NO2", "CO", "SO2"],
                    "update_frequency": "hourly",
                    "spatial_resolution": "point measurement",
                    "reliability": 0.95,
                    "status": "active"
                })
            
            # OpenAQ (Global)
            data_sources.append({
                "name": "OpenAQ",
                "type": "ground_station", 
                "parameters": ["PM2.5", "PM10", "O3", "NO2", "CO", "SO2"],
                "update_frequency": "varies",
                "spatial_resolution": "point measurement",
                "reliability": 0.80,
                "status": "active"
            })
            
            # Weather data
            data_sources.append({
                "name": "OpenWeatherMap",
                "type": "weather",
                "parameters": ["Temperature", "Humidity", "Wind", "Pressure"],
                "update_frequency": "3 hours",
                "spatial_resolution": "2.5 x 2.5 km",
                "reliability": 0.90,
                "status": "active"
            })
            
            return data_sources
            
        except Exception as e:
            logger.error(f"Error getting data sources for location {location_id}: {e}")
            return []
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    def _get_region(self, country: str) -> str:
        """Get region from country name."""
        region_mapping = {
            "United States": "North America",
            "Canada": "North America", 
            "Mexico": "North America",
            "United Kingdom": "Europe",
            "France": "Europe",
            "Germany": "Europe",
            "China": "Asia",
            "Japan": "Asia",
            "India": "Asia",
            "Brazil": "South America",
            "Australia": "Oceania"
        }
        return region_mapping.get(country, "Other")
    
    def _get_sample_locations(self) -> List[Location]:
        """Get sample monitoring locations."""
        return [
            Location(
                id=1,
                name="Los Angeles, CA",
                latitude=34.0522,
                longitude=-118.2437,
                country="United States",
                state="California",
                city="Los Angeles",
                postal_code="90210",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=2,
                name="New York, NY",
                latitude=40.7128,
                longitude=-74.0060,
                country="United States",
                state="New York",
                city="New York",
                postal_code="10001",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=3,
                name="Houston, TX",
                latitude=29.7604,
                longitude=-95.3698,
                country="United States",
                state="Texas",
                city="Houston",
                postal_code="77001",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=4,
                name="Toronto, ON",
                latitude=43.6532,
                longitude=-79.3832,
                country="Canada",
                state="Ontario",
                city="Toronto",
                postal_code="M5H 2N2",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=5,
                name="Mexico City",
                latitude=19.4326,
                longitude=-99.1332,
                country="Mexico",
                state="Mexico City",
                city="Mexico City",
                postal_code="06600",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=6,
                name="Denver, CO",
                latitude=39.7392,
                longitude=-104.9903,
                country="United States",
                state="Colorado",
                city="Denver",
                postal_code="80201",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=7,
                name="Chicago, IL",
                latitude=41.8781,
                longitude=-87.6298,
                country="United States",
                state="Illinois",
                city="Chicago",
                postal_code="60601",
                is_active=True,
                created_at=datetime.utcnow()
            ),
            Location(
                id=8,
                name="Atlanta, GA",
                latitude=33.7490,
                longitude=-84.3880,
                country="United States",
                state="Georgia",
                city="Atlanta",
                postal_code="30301",
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]


# Global service instance
location_service = LocationService()
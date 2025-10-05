# API Endpoints Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the API does not require authentication for development. In production, you would implement API key authentication.

## Air Quality Endpoints

### Get Current Air Quality
```http
GET /api/v1/air-quality/current?latitude={lat}&longitude={lon}
```

**Parameters:**
- `latitude` (float): Location latitude (-90 to 90)
- `longitude` (float): Location longitude (-180 to 180)  
- `radius_km` (float, optional): Search radius in kilometers (default: 10)
- `sources` (array, optional): Data sources to include (TEMPO, EPA, OpenAQ, etc.)

**Response:**
```json
{
  "location": {
    "id": 0,
    "name": "Location 34.052, -118.244",
    "latitude": 34.052,
    "longitude": -118.244,
    "country": "Unknown"
  },
  "current_measurement": {
    "source": "TEMPO",
    "timestamp": "2025-10-04T...",
    "pm25": 25.5,
    "no2": 45.2,
    "aqi": 75,
    "aqi_category": "Moderate"
  },
  "weather": {
    "temperature": 22.5,
    "humidity": 65,
    "wind_speed": 3.2
  },
  "predictions": [],
  "active_alerts": []
}
```

### Get Air Quality Forecast
```http
GET /api/v1/air-quality/forecast?latitude={lat}&longitude={lon}&hours=24
```

**Parameters:**
- `latitude` (float): Location latitude
- `longitude` (float): Location longitude
- `hours` (int): Forecast horizon in hours (1-168)
- `model_version` (string, optional): Specific model version

### Get Historical Data
```http
GET /api/v1/air-quality/historical?latitude={lat}&longitude={lon}&start_date={date}&end_date={date}
```

**Parameters:**
- `latitude` (float): Location latitude
- `longitude` (float): Location longitude
- `start_date` (datetime): Start of time range (ISO format)
- `end_date` (datetime): End of time range (ISO format)
- `pollutant` (string, optional): Specific pollutant (pm25, no2, o3, etc.)
- `sources` (array, optional): Data sources to include
- `limit` (int): Maximum records (1-10000, default: 1000)

### Get AQI Information
```http
GET /api/v1/air-quality/aqi-info
```

Returns AQI categories, ranges, colors, and health recommendations.

### Compare Data Sources
```http
GET /api/v1/air-quality/compare-sources?latitude={lat}&longitude={lon}&pollutant=pm25
```

## Location Endpoints

### Get Locations
```http
GET /api/v1/locations/
```

**Parameters:**
- `country` (string, optional): Filter by country
- `state` (string, optional): Filter by state/province
- `active_only` (bool): Only return active locations (default: true)
- `limit` (int): Maximum locations (1-1000, default: 100)

### Get Location Details
```http
GET /api/v1/locations/{location_id}
```

### Find Nearby Locations
```http
GET /api/v1/locations/search/nearby?latitude={lat}&longitude={lon}&radius_km=50
```

### Get Global Coverage
```http
GET /api/v1/locations/coverage/global
```

## Alert Endpoints

### Get Active Alerts
```http
GET /api/v1/alerts/active
```

**Parameters:**
- `latitude` (float, optional): Filter by latitude
- `longitude` (float, optional): Filter by longitude
- `radius_km` (float): Search radius (default: 50)
- `severity` (string, optional): Filter by severity (low, moderate, high, very_high)
- `alert_type` (string, optional): Filter by alert type

### Subscribe to Alerts
```http
POST /api/v1/alerts/subscribe
```

**Body:**
```json
{
  "contact_method": "email",
  "contact_info": "user@example.com",
  "locations": [1, 2, 3],
  "severity_threshold": "moderate",
  "alert_types": ["health", "visibility"]
}
```

### Get Alert Statistics
```http
GET /api/v1/alerts/statistics?days=30
```

## Status Endpoints

### Health Check
```http
GET /health
```

Returns API health status.

### API Information
```http
GET /
```

Returns basic API information and documentation links.

## Error Responses

All endpoints return errors in this format:
```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (no data available)
- `422`: Validation Error (invalid input format)
- `500`: Internal Server Error

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per IP

## Data Sources

### TEMPO Satellite
- Coverage: North America
- Parameters: NO2, O3, HCHO, Aerosols
- Resolution: 2.1 x 4.4 km
- Update: Hourly

### EPA AirNow
- Coverage: United States
- Parameters: PM2.5, PM10, O3, NO2, CO, SO2
- Update: Hourly

### OpenAQ
- Coverage: Global
- Parameters: PM2.5, PM10, O3, NO2, CO, SO2
- Update: Varies by station

### Weather Data
- Source: OpenWeatherMap, NOAA
- Parameters: Temperature, humidity, wind, pressure
- Update: 3 hours

## Interactive Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
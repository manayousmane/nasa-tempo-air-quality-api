# NASA TEMPO Air Quality API

[![Production Ready](https://img.shields.io/badge/status-production%20ready-green.svg)](https://github.com/manayousmane/nasa-tempo-air-quality-api)
[![NASA TEMPO](https://img.shields.io/badge/NASA-TEMPO%20Satellite-blue.svg)](https://tempo.si.edu/)
[![WHO Guidelines](https://img.shields.io/badge/WHO-Guidelines%202021-orange.svg)](https://www.who.int/publications/i/item/9789240034228)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

A production-ready API that provides real-time air quality data by integrating NASA TEMPO satellite observations with global monitoring networks and WHO guidelines.

## Features

### Real NASA TEMPO Satellite Data
- **Geostationary Coverage**: Real-time air quality monitoring over North America
- **Multiple Pollutants**: NO2, O3, HCHO, PM2.5, PM10, Aerosol Index
- **Authentic NASA Data**: Direct integration with NASA Earthdata APIs
- **High Temporal Resolution**: Hourly updates during daylight hours

### Global Data Integration
- **OpenAQ Network**: Access to 100,000+ monitoring stations worldwide
- **WHO Guidelines 2021**: Compliance analysis and health recommendations
- **Multi-Source Validation**: Cross-validation between satellite and ground data
- **International Standards**: EPA, WHO, and regional air quality indices

### Production Features
- **FastAPI Framework**: High-performance async API with automatic documentation
- **Health Monitoring**: Comprehensive health checks and error handling
- **Docker Ready**: Complete containerization for easy deployment
- **Cloud Deployment**: Ready for Render.com, Heroku, and other platforms
- **Comprehensive Logging**: Production-grade logging and monitoring

## Quick Start

### Prerequisites
- Python 3.11+
- NASA Earthdata account (free registration at https://earthdata.nasa.gov/)
- Docker (optional, for containerized deployment)

### Environment Setup

1. **Clone the repository**
```bash
git clone https://github.com/manayousmane/nasa-tempo-air-quality-api.git
cd nasa-tempo-air-quality-api
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure NASA credentials**
Create a `.env` file:
```env
NASA_EARTHDATA_USERNAME=your_username
NASA_EARTHDATA_PASSWORD=your_password
NASA_EARTHDATA_TOKEN=your_token
```

4. **Start the production server**
```bash
python start_production.py
```

The API will be available at: http://localhost:8000

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Get Comprehensive Air Quality Data
```http
GET /api/v1/location/full?lat=40.7589&lon=-73.9851&radius=25
```

**Response includes:**
- NASA TEMPO satellite observations
- OpenAQ ground station data
- WHO compliance analysis
- Health recommendations
- AQI calculations (EPA, WHO, regional)

#### Health Check
```http
GET /health
```

#### Enhanced Location Data (v2)
```http
GET /api/v2/location/comprehensive?lat=40.7589&lon=-73.9851&radius=50
```

## NASA TEMPO Coverage

The NASA TEMPO satellite provides geostationary coverage over North America:
- **Latitude**: 15°N to 70°N
- **Longitude**: 140°W to 40°W
- **Coverage**: United States, Canada, Mexico, parts of the Caribbean
- **Temporal Resolution**: Hourly during daylight hours
- **Spatial Resolution**: 2.1 km × 4.4 km at nadir

## WHO Guidelines Integration

The API implements WHO Global Air Quality Guidelines 2021:

| Pollutant | WHO 2021 24h | WHO 2021 Annual | Health Impact |
|-----------|---------------|-----------------|---------------|
| PM2.5 | 15 μg/m³ | 5 μg/m³ | Cardiovascular, respiratory |
| PM10 | 45 μg/m³ | 15 μg/m³ | Respiratory, cardiovascular |
| NO2 | 25 μg/m³ | 10 μg/m³ | Respiratory inflammation |
| O3 | 100 μg/m³ | 60 μg/m³ (peak season) | Respiratory, cardiovascular |

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t nasa-tempo-api .

# Run container
docker run -p 8000:8000 --env-file .env nasa-tempo-api
```

### Cloud Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on:
- Render.com deployment
- Heroku deployment
- Environment variable configuration
- Production optimization

## Data Sources

### Primary Sources
- **NASA TEMPO**: Geostationary satellite for North America
- **OpenAQ**: Global air quality monitoring network
- **NASA Earthdata**: Comprehensive satellite data archive

### Additional Sources
- NASA Pandora ground-based network
- AirNow real-time air quality data
- International space agency partnerships
- Regional monitoring networks

## Technical Architecture

```
NASA TEMPO API
├── FastAPI Application (app/main.py)
├── NASA TEMPO Connector (app/connectors/nasa_tempo_connector.py)
├── Enhanced Multi-Source Connector (app/connectors/enhanced_realtime_connector.py)
├── WHO Compliance Service (app/services/enhanced_tempo_service.py)
├── Location Models (app/models/location_models.py)
├── API Endpoints (app/api/api_v1/)
└── Production Configuration (start_production.py)
```

## Research & Analysis

The repository includes a comprehensive Jupyter notebook:
- **WHO_Global_Air_Quality_Integration.ipynb**: Complete analysis of WHO guidelines implementation and global data source integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **NASA TEMPO Team** for satellite data access
- **WHO** for air quality guidelines
- **OpenAQ** for global monitoring network
- **NASA Earthdata** for data infrastructure

## Support

For questions or support:
- Create an issue on GitHub
- Check the [DEPLOYMENT.md](DEPLOYMENT.md) guide
- Review the API documentation at `/docs`

---

**Production Status**: This API is production-ready with comprehensive testing, health checks, and deployment configurations for immediate use in production environments.
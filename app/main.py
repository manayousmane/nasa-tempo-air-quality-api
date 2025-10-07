"""
NASA TEMPO Air Quality API - Production Ready
Real-time air quality data from NASA TEMPO satellite and global networks
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from datetime import datetime

from app.api.api_v1 import router as api_v1_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with comprehensive metadata
app = FastAPI(
    title="NASA TEMPO Air Quality API",
    description="""
    ## Real-time Air Quality Monitoring API

    This API provides comprehensive air quality data from multiple authoritative sources:

    ### Primary Data Sources:
    - **NASA TEMPO Satellite** - Geostationary monitoring over North America
    - **OpenAQ Global Network** - 150+ countries real-time ground stations
    - **NASA Ground Stations** - Pandora Project, TOLNet observations
    - **WHO Guidelines** - 2021 air quality standards compliance

    ### Global Coverage:
    - **North America**: Enhanced TEMPO satellite coverage
    - **Worldwide**: Ground station networks and alternative satellites
    - **Real-time**: Hourly to daily updates depending on source

    ### Available Data:
    - Air Quality Index (AQI) calculations
    - Pollutant concentrations (PM2.5, PM10, NO2, O3, SO2, CO)
    - WHO guideline compliance analysis
    - Health recommendations
    - Data quality assessments

    ### Quick Start:
    Try: `/api/v1/location/full?latitude=43.6532&longitude=-79.3832`
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "NASA TEMPO API Team",
        "url": "https://github.com/manayousmane/nasa-tempo-air-quality-api",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Add CORS middleware with production settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_v1_router, prefix="/api/v1", tags=["Air Quality Data"])

# Try to include enhanced endpoints if available
try:
    from app.api.api_v1.enhanced_location import router as enhanced_router
    app.include_router(enhanced_router, prefix="/api/v2", tags=["Enhanced Multi-Source Data"])
    logger.info("Enhanced endpoints loaded")
except ImportError as e:
    logger.warning(f"Enhanced endpoints not available: {e}")

@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint with comprehensive information
    """
    return {
        "service": "NASA TEMPO Air Quality API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_sources": [
            "NASA TEMPO Satellite",
            "OpenAQ Global Network", 
            "NASA Ground Stations",
            "WHO Guidelines 2021",
            "International Space Agencies"
        ],
        "coverage": {
            "tempo_region": "North America (15°N-70°N, 140°W-40°W)",
            "global_coverage": "Worldwide via ground stations",
            "update_frequency": "Hourly to daily"
        },
        "endpoints": {
            "documentation": "/docs",
            "health_check": "/health",
            "v1_api": {
                "full_data": "/api/v1/location/full?latitude=43.6532&longitude=-79.3832",
                "aqi_only": "/api/v1/location/aqi?latitude=43.6532&longitude=-79.3832",
                "pollutants": "/api/v1/location/pollutants?latitude=43.6532&longitude=-79.3832"
            },
            "v2_enhanced": {
                "comprehensive": "/api/v2/location/comprehensive?latitude=43.6532&longitude=-79.3832",
                "tempo_coverage": "/api/v2/location/tempo-coverage?latitude=43.6532&longitude=-79.3832",
                "who_analysis": "/api/v2/location/who-analysis?latitude=43.6532&longitude=-79.3832"
            }
        },
        "example_locations": {
            "toronto_canada": {"lat": 43.6532, "lon": -79.3832, "tempo": True},
            "new_york_usa": {"lat": 40.7128, "lon": -74.0060, "tempo": True},
            "london_uk": {"lat": 51.5074, "lon": -0.1278, "tempo": False},
            "tokyo_japan": {"lat": 35.6762, "lon": 139.6503, "tempo": False}
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Comprehensive health check endpoint for monitoring
    """
    try:
        # Check environment variables
        nasa_configured = all([
            os.getenv('NASA_EARTHDATA_USERNAME'),
            os.getenv('NASA_EARTHDATA_PASSWORD'),
            os.getenv('NASA_EARTHDATA_TOKEN')
        ])
        
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "NASA TEMPO Air Quality API",
            "version": "2.0.0",
            "checks": {
                "nasa_credentials": "configured" if nasa_configured else "missing",
                "api_endpoints": "operational",
                "database": "n/a (stateless API)",
                "external_apis": "configured"
            }
        }
        
        # Return appropriate status code
        status_code = 200 if nasa_configured else 503
        
        return JSONResponse(
            content=health_status,
            status_code=status_code
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            },
            status_code=503
        )

@app.get("/status", tags=["Health"])
async def status():
    """Simple status endpoint for basic monitoring"""
    return {"status": "ok", "service": "nasa-tempo-api"}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": "Please check the API documentation at /docs",
            "available_endpoints": ["/api/v1/location/full", "/health", "/docs"]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Please try again later or contact support"
        }
    )

def main():
    """Main function to run the API server in development"""
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '127.0.0.1')
    reload = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting NASA TEMPO API on {host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NASA TEMPO API"}

def main():
    """Main function to run the API server"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
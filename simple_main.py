"""
NASA TEMPO Air Quality API - Simplified for Render deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Create simple FastAPI app
app = FastAPI(
    title="NASA TEMPO Air Quality API",
    description="Air quality prediction API using NASA TEMPO satellite data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Simple CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "🛰️ NASA TEMPO Air Quality Prediction API",
        "version": "1.0.0",
        "status": "deployed_on_render",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "health": "/health",
            "docs": "/docs", 
            "locations": "/api/v1/locations"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "service": "NASA TEMPO Air Quality API",
        "python_version": "3.11+",
        "deployment": "render"
    }

@app.get("/api/v1/locations")
async def get_locations():
    """Sample locations endpoint."""
    return {
        "available_locations": [
            "Toronto", "Montreal", "Vancouver",
            "New York", "Los Angeles", "Chicago",
            "California", "Texas", "Florida"
        ],
        "total": 9,
        "note": "This is a simplified version for Render deployment demo"
    }

@app.get("/api/v1/location/{location_name}")
async def get_location_data(location_name: str):
    """Sample location data endpoint."""
    # Sample data for demo
    sample_data = {
        "name": location_name.title(),
        "coordinates": {
            "latitude": 43.65,
            "longitude": -79.38
        },
        "aqi": 45.2,
        "pm25": 12.8,
        "status": "demo_data",
        "note": "This is sample data for Render deployment demo"
    }
    
    return sample_data

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("simple_main:app", host="0.0.0.0", port=port)
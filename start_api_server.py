"""
Simple server to test NASA TEMPO API
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("Starting NASA TEMPO API Server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Test endpoint: http://localhost:8000/api/v1/location/full?latitude=43.6532&longitude=-79.3832")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
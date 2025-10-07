#!/usr/bin/env python3
"""
NASA TEMPO Air Quality API - Production Startup Script
Optimized for deployment with health checks and monitoring
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('nasa_tempo_api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check required environment variables and dependencies"""
    
    # Load .env file first
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'NASA_EARTHDATA_USERNAME',
        'NASA_EARTHDATA_PASSWORD',
        'NASA_EARTHDATA_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing NASA environment variables: {missing_vars}")
        logger.warning("Running in limited mode - some NASA TEMPO features may not be available")
        logger.warning("For full functionality, configure NASA credentials at https://earthdata.nasa.gov/")
        # Don't exit - allow the app to start in limited mode
    
    logger.info("Environment variables configured")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import aiohttp
        import geopy
        import numpy
        import pandas
        logger.info("All required dependencies available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

async def health_check():
    """Perform API health check"""
    try:
        from app.connectors.enhanced_realtime_connector import EnhancedRealTimeConnector
        
        # Test connector initialization
        connector = EnhancedRealTimeConnector(
            nasa_username=os.getenv('NASA_EARTHDATA_USERNAME'),
            nasa_password=os.getenv('NASA_EARTHDATA_PASSWORD'),
            nasa_token=os.getenv('NASA_EARTHDATA_TOKEN')
        )
        
        # Test TEMPO coverage check
        toronto_coverage = connector.is_in_tempo_coverage(43.6532, -79.3832)
        logger.info(f"TEMPO coverage check: {toronto_coverage}")
        
        # Test authentication
        async with connector as conn:
            auth_result = await conn.authenticate()
            logger.info(f"NASA authentication: {auth_result}")
        
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("Starting NASA TEMPO Air Quality API")
    logger.info("="*50)
    
    # Pre-flight checks - continue even if some fail
    check_environment()  # Remove the sys.exit(1) dependency
    
    if not check_dependencies():
        sys.exit(1)
    
    # Run health check
    logger.info("Running health checks...")
    try:
        health_ok = asyncio.run(health_check())
        if not health_ok:
            logger.warning("Health check failed, but continuing startup")
    except Exception as e:
        logger.warning(f"Health check error: {e}")
    
    # Import and start the FastAPI app
    try:
        import uvicorn
        from app.main import app
        
        # Server configuration
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 8000))
        reload = os.getenv('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Starting server on http://{host}:{port}")
        logger.info(f"API documentation: http://{host}:{port}/docs")
        logger.info(f"Reload mode: {reload}")
        logger.info("="*50)
        
        # Start the server
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=[str(project_root)] if reload else None,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
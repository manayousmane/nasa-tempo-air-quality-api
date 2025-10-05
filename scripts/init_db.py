"""
Database initialization script.
"""
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.database import Base
from app.core.logging import get_logger

logger = get_logger(__name__)


async def init_database():
    """Initialize the database with tables."""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_database())
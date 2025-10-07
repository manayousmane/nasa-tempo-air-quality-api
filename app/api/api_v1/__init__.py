"""
API v1 router configuration
"""
from fastapi import APIRouter

from . import location

router = APIRouter()

# Include location endpoints
router.include_router(location.router, prefix="/location", tags=["location"])
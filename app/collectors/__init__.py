"""
Collectors package for NASA Air Quality API

This package contains various data collectors for air quality information:
- OpenSourceAirQualityCollector: Free APIs collector
- NorthAmericaAirQualityTester: Regional specialized collector
"""

from .open_source_collector import OpenSourceAirQualityCollector
# Temporarily commented out for deployment
# from .test_north_america_states import NorthAmericaAirQualityTester

__all__ = [
    'OpenSourceAirQualityCollector',
    # 'NorthAmericaAirQualityTester'
]
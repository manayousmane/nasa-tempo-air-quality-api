"""
Alert management API endpoints.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.models.schemas import Alert, AlertCreate, AlertSeverity
from app.services.alert_service import AlertService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_alert_service() -> AlertService:
    """Dependency to get alert service."""
    return AlertService()


@router.get("/active", response_model=List[Alert])
async def get_active_alerts(
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Filter by latitude"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Filter by longitude"),
    radius_km: float = Query(50, ge=0.1, le=500, description="Search radius in kilometers"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity level"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    service: AlertService = Depends(get_alert_service)
):
    """
    Get currently active air quality alerts.
    
    - **latitude**: Optional filter by latitude (-90 to 90)
    - **longitude**: Optional filter by longitude (-180 to 180)
    - **radius_km**: Search radius when lat/lon provided (0.1 to 500)
    - **severity**: Filter by alert severity (low, moderate, high, very_high)
    - **alert_type**: Filter by alert type (health, visibility, etc.)
    - **limit**: Maximum number of alerts to return (1 to 1000)
    
    Returns list of active alerts with location and severity information.
    """
    try:
        alerts = await service.get_active_alerts(
            latitude=latitude,
            longitude=longitude, 
            radius_km=radius_km,
            severity=severity,
            alert_type=alert_type,
            limit=limit
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/location/{location_id}", response_model=List[Alert])
async def get_location_alerts(
    location_id: int,
    active_only: bool = Query(True, description="Only return active alerts"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of alerts"),
    service: AlertService = Depends(get_alert_service)
):
    """
    Get alerts for a specific location.
    
    - **location_id**: Unique location identifier
    - **active_only**: Only return currently active alerts
    - **limit**: Maximum number of alerts to return (1 to 500)
    
    Returns alerts for the specified location ordered by severity and time.
    """
    try:
        alerts = await service.get_location_alerts(
            location_id=location_id,
            active_only=active_only,
            limit=limit
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts for location {location_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/subscribe")
async def subscribe_to_alerts(
    subscription_data: dict = Body(...),
    service: AlertService = Depends(get_alert_service)
):
    """
    Subscribe to air quality alerts for specified locations and criteria.
    
    - **subscription_data**: Subscription configuration including:
        - contact_method: email, sms, webhook
        - contact_info: email address, phone number, or webhook URL
        - locations: list of location IDs or coordinates
        - severity_threshold: minimum severity level for alerts
        - alert_types: types of alerts to receive
        - schedule: when to receive alerts (always, business_hours, etc.)
    
    Returns subscription confirmation with unique subscription ID.
    """
    try:
        # Validate required fields
        required_fields = ['contact_method', 'contact_info', 'locations']
        for field in required_fields:
            if field not in subscription_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate contact method
        valid_methods = ['email', 'sms', 'webhook']
        if subscription_data['contact_method'] not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid contact method. Must be one of: {valid_methods}"
            )
        
        subscription = await service.create_subscription(subscription_data)
        
        return {
            "message": "Subscription created successfully",
            "subscription_id": subscription["id"],
            "status": "active",
            "contact_method": subscription["contact_method"],
            "locations": subscription["locations"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert subscription: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/subscription/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    service: AlertService = Depends(get_alert_service)
):
    """
    Get details of an alert subscription.
    
    - **subscription_id**: Unique subscription identifier
    
    Returns subscription details and current status.
    """
    try:
        subscription = await service.get_subscription(subscription_id)
        
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found"
            )
        
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/subscription/{subscription_id}")
async def unsubscribe_from_alerts(
    subscription_id: str,
    service: AlertService = Depends(get_alert_service)
):
    """
    Unsubscribe from air quality alerts.
    
    - **subscription_id**: Unique subscription identifier
    
    Returns confirmation of subscription cancellation.
    """
    try:
        success = await service.delete_subscription(subscription_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found"
            )
        
        return {
            "message": "Subscription cancelled successfully",
            "subscription_id": subscription_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test")
async def test_alert_system(
    test_data: dict = Body(...),
    service: AlertService = Depends(get_alert_service)
):
    """
    Test the alert system with sample data.
    
    - **test_data**: Test configuration including:
        - contact_method: how to send test alert
        - contact_info: where to send test alert
        - alert_type: type of test alert
    
    Returns test result and delivery status.
    
    Note: This endpoint is for testing purposes and administrative use.
    """
    try:
        result = await service.test_alert_system(test_data)
        return result
        
    except Exception as e:
        logger.error(f"Error testing alert system: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{subscription_id}")
async def get_alert_history(
    subscription_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for history"),
    end_date: Optional[datetime] = Query(None, description="End date for history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    service: AlertService = Depends(get_alert_service)
):
    """
    Get alert history for a subscription.
    
    - **subscription_id**: Unique subscription identifier
    - **start_date**: Optional start date for history filter
    - **end_date**: Optional end date for history filter
    - **limit**: Maximum number of alerts to return (1 to 1000)
    
    Returns historical alerts sent to this subscription.
    """
    try:
        # Validate subscription exists
        subscription = await service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found"
            )
        
        # Validate date range
        if start_date and end_date and end_date <= start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date"
            )
        
        history = await service.get_alert_history(
            subscription_id=subscription_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "subscription_id": subscription_id,
            "start_date": start_date,
            "end_date": end_date,
            "total_alerts": len(history),
            "alerts": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert history for {subscription_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/statistics")
async def get_alert_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    service: AlertService = Depends(get_alert_service)
):
    """
    Get alert system statistics.
    
    - **days**: Number of days to include in statistics (1 to 365)
    
    Returns alert frequency, severity distribution, and system performance metrics.
    """
    try:
        stats = await service.get_alert_statistics(days)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
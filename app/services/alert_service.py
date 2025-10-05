"""
Alert service for managing air quality alerts and notifications.
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.models.schemas import Alert, AlertCreate, AlertSeverity
from app.core.logging import get_logger

logger = get_logger(__name__)


class AlertService:
    """Service for alert operations."""
    
    def __init__(self):
        # In a real implementation, these would be stored in database/cache
        self._active_alerts = self._get_sample_alerts()
        self._subscriptions = {}
        self._alert_history = {}
    
    async def get_active_alerts(self,
                              latitude: Optional[float] = None,
                              longitude: Optional[float] = None,
                              radius_km: float = 50,
                              severity: Optional[AlertSeverity] = None,
                              alert_type: Optional[str] = None,
                              limit: int = 100) -> List[Alert]:
        """
        Get currently active alerts.
        
        Args:
            latitude: Optional filter by latitude
            longitude: Optional filter by longitude
            radius_km: Search radius when coordinates provided
            severity: Filter by severity level
            alert_type: Filter by alert type
            limit: Maximum number of alerts
        
        Returns:
            List of active alerts
        """
        try:
            alerts = [alert for alert in self._active_alerts if alert.is_active]
            
            # Filter by severity
            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]
            
            # Filter by alert type
            if alert_type:
                alerts = [alert for alert in alerts if alert.alert_type == alert_type]
            
            # Geographic filtering would require location lookup
            # For now, return all matching alerts
            
            # Sort by severity and time
            severity_order = {"very_high": 4, "high": 3, "moderate": 2, "low": 1}
            alerts.sort(key=lambda x: (
                severity_order.get(x.severity.value, 0),
                x.created_at
            ), reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def get_location_alerts(self,
                                location_id: int,
                                active_only: bool = True,
                                limit: int = 50) -> List[Alert]:
        """
        Get alerts for a specific location.
        
        Args:
            location_id: Location identifier
            active_only: Only return active alerts
            limit: Maximum number of alerts
        
        Returns:
            List of alerts for the location
        """
        try:
            alerts = [alert for alert in self._active_alerts if alert.location_id == location_id]
            
            if active_only:
                alerts = [alert for alert in alerts if alert.is_active]
            
            # Sort by severity and time
            severity_order = {"very_high": 4, "high": 3, "moderate": 2, "low": 1}
            alerts.sort(key=lambda x: (
                severity_order.get(x.severity.value, 0),
                x.created_at
            ), reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting alerts for location {location_id}: {e}")
            return []
    
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new alert subscription.
        
        Args:
            subscription_data: Subscription configuration
        
        Returns:
            Created subscription details
        """
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = {
                "id": subscription_id,
                "contact_method": subscription_data["contact_method"],
                "contact_info": subscription_data["contact_info"],
                "locations": subscription_data["locations"],
                "severity_threshold": subscription_data.get("severity_threshold", "moderate"),
                "alert_types": subscription_data.get("alert_types", ["health", "visibility"]),
                "schedule": subscription_data.get("schedule", "always"),
                "status": "active",
                "created_at": datetime.utcnow(),
                "last_alert_sent": None
            }
            
            self._subscriptions[subscription_id] = subscription
            
            logger.info(f"Created subscription {subscription_id}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            raise
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription details.
        
        Args:
            subscription_id: Subscription identifier
        
        Returns:
            Subscription details or None if not found
        """
        try:
            return self._subscriptions.get(subscription_id)
            
        except Exception as e:
            logger.error(f"Error getting subscription {subscription_id}: {e}")
            return None
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete a subscription.
        
        Args:
            subscription_id: Subscription identifier
        
        Returns:
            True if subscription was deleted
        """
        try:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                logger.info(f"Deleted subscription {subscription_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting subscription {subscription_id}: {e}")
            return False
    
    async def test_alert_system(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test the alert system.
        
        Args:
            test_data: Test configuration
        
        Returns:
            Test results
        """
        try:
            contact_method = test_data.get("contact_method", "email")
            contact_info = test_data.get("contact_info")
            alert_type = test_data.get("alert_type", "test")
            
            # Simulate sending test alert
            test_result = {
                "test_id": str(uuid.uuid4()),
                "contact_method": contact_method,
                "contact_info": contact_info,
                "alert_type": alert_type,
                "status": "success",
                "delivery_time": datetime.utcnow(),
                "message": "Test alert sent successfully"
            }
            
            # In a real implementation, this would actually send the alert
            if contact_method == "email":
                test_result["delivery_method"] = "SMTP"
            elif contact_method == "sms":
                test_result["delivery_method"] = "SMS Gateway"
            elif contact_method == "webhook":
                test_result["delivery_method"] = "HTTP POST"
            
            logger.info(f"Test alert sent: {test_result['test_id']}")
            return test_result
            
        except Exception as e:
            logger.error(f"Error testing alert system: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def get_alert_history(self,
                              subscription_id: str,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alert history for a subscription.
        
        Args:
            subscription_id: Subscription identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of alerts
        
        Returns:
            List of historical alerts
        """
        try:
            # Get history for subscription
            history = self._alert_history.get(subscription_id, [])
            
            # Apply date filters
            filtered_history = []
            for alert in history:
                alert_date = alert.get("sent_at")
                if not alert_date:
                    continue
                
                if start_date and alert_date < start_date:
                    continue
                
                if end_date and alert_date > end_date:
                    continue
                
                filtered_history.append(alert)
            
            # Sort by date (newest first)
            filtered_history.sort(key=lambda x: x.get("sent_at", datetime.min), reverse=True)
            
            return filtered_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return []
    
    async def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get alert system statistics.
        
        Args:
            days: Number of days for statistics
        
        Returns:
            Alert statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count alerts by severity
            severity_counts = {"low": 0, "moderate": 0, "high": 0, "very_high": 0}
            type_counts = {}
            total_alerts = 0
            
            for alert in self._active_alerts:
                if alert.created_at >= cutoff_date:
                    total_alerts += 1
                    severity_counts[alert.severity.value] += 1
                    type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
            
            # Calculate subscription statistics
            active_subscriptions = len([s for s in self._subscriptions.values() if s["status"] == "active"])
            
            # Calculate delivery statistics (placeholder)
            delivery_stats = {
                "total_sent": total_alerts * 2,  # Approximate
                "success_rate": 0.95,
                "avg_delivery_time": "2.3 seconds"
            }
            
            return {
                "period_days": days,
                "total_alerts": total_alerts,
                "severity_distribution": severity_counts,
                "alert_type_distribution": type_counts,
                "active_subscriptions": active_subscriptions,
                "delivery_statistics": delivery_stats,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}
    
    async def check_and_send_alerts(self):
        """
        Check conditions and send alerts to subscribers.
        
        This method would be called periodically by a scheduler.
        """
        try:
            logger.info("Checking for alert conditions")
            
            # Check each subscription
            for subscription_id, subscription in self._subscriptions.items():
                if subscription["status"] != "active":
                    continue
                
                # Check if any conditions warrant an alert
                should_alert = await self._evaluate_alert_conditions(subscription)
                
                if should_alert:
                    await self._send_alert_to_subscriber(subscription_id, subscription)
            
        except Exception as e:
            logger.error(f"Error checking and sending alerts: {e}")
    
    async def _evaluate_alert_conditions(self, subscription: Dict[str, Any]) -> bool:
        """
        Evaluate if alert conditions are met for a subscription.
        
        Args:
            subscription: Subscription configuration
        
        Returns:
            True if alert should be sent
        """
        try:
            # This would check current air quality conditions against thresholds
            # For now, return False (no alerts)
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert conditions: {e}")
            return False
    
    async def _send_alert_to_subscriber(self, subscription_id: str, subscription: Dict[str, Any]):
        """
        Send alert to a subscriber.
        
        Args:
            subscription_id: Subscription identifier
            subscription: Subscription configuration
        """
        try:
            # This would implement the actual alert sending logic
            logger.info(f"Sending alert to subscription {subscription_id}")
            
            # Update last alert sent timestamp
            subscription["last_alert_sent"] = datetime.utcnow()
            
            # Add to history
            if subscription_id not in self._alert_history:
                self._alert_history[subscription_id] = []
            
            self._alert_history[subscription_id].append({
                "alert_id": str(uuid.uuid4()),
                "sent_at": datetime.utcnow(),
                "contact_method": subscription["contact_method"],
                "severity": "high",
                "message": "Air quality alert for your subscribed locations"
            })
            
        except Exception as e:
            logger.error(f"Error sending alert to subscriber {subscription_id}: {e}")
    
    def _get_sample_alerts(self) -> List[Alert]:
        """Get sample active alerts."""
        return [
            Alert(
                id=1,
                location_id=1,  # Los Angeles
                alert_type="health",
                severity=AlertSeverity.HIGH,
                title="High PM2.5 Levels in Los Angeles",
                message="PM2.5 levels have exceeded unhealthy thresholds. Sensitive individuals should avoid outdoor activities.",
                start_time=datetime.utcnow() - timedelta(hours=2),
                is_active=True,
                triggered_by="PM2.5 threshold",
                threshold_value=55.0,
                actual_value=68.2,
                created_at=datetime.utcnow() - timedelta(hours=2)
            ),
            Alert(
                id=2,
                location_id=3,  # Houston
                alert_type="visibility",
                severity=AlertSeverity.MODERATE,
                title="Reduced Visibility Due to Haze",
                message="Atmospheric haze is reducing visibility. Exercise caution while driving.",
                start_time=datetime.utcnow() - timedelta(hours=1),
                is_active=True,
                triggered_by="Visibility threshold",
                threshold_value=10.0,
                actual_value=7.5,
                created_at=datetime.utcnow() - timedelta(hours=1)
            ),
            Alert(
                id=3,
                location_id=2,  # New York
                alert_type="health",
                severity=AlertSeverity.MODERATE,
                title="Elevated Ozone Levels",
                message="Ground-level ozone concentrations are elevated. Limit prolonged outdoor exertion.",
                start_time=datetime.utcnow() - timedelta(minutes=30),
                is_active=True,
                triggered_by="O3 threshold",
                threshold_value=70.0,
                actual_value=78.3,
                created_at=datetime.utcnow() - timedelta(minutes=30)
            )
        ]


# Global service instance
alert_service = AlertService()
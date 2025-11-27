"""
Push Notification Repository - Business logic for push notification operations
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services.push_service import PushNotificationServiceFactory
from src.utils.libs.logging import logging
from src.utils.helpers.errors import BadRequestError, ServiceUnavailableError


class PushNotificationRepository:
    """Repository for Push Notification operations"""
    
    def __init__(self):
        self.factory = PushNotificationServiceFactory()
    
    async def send_single_push(self, device_token: str, title: str, body: str,
                              data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a single push notification
        
        Args:
            device_token: Firebase device token
            title: Notification title
            body: Notification body
            data: Additional data payload (optional)
        
        Returns:
            Dictionary with send status
        """
        try:
            # Validate inputs
            if not device_token or not title or not body:
                raise BadRequestError(
                    message="Device token, title, and body are required",
                    verboseMessage="device_token, title, and body fields must all be provided"
                )
            
            logging.info(f"Sending single push notification to device: {device_token}")
            
            # Get Firebase provider
            provider = self.factory.get_provider("firebase")
            result = await provider.send(device_token, title, body, data)
            
            return {
                "success": result.get("status") == "sent",
                "data": result
            }
            
        except BadRequestError:
            raise
        except Exception as e:
            logging.error(f"Push notification send failed: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to send push notification",
                verboseMessage=str(e)
            )
    
    async def send_bulk_push(self, device_tokens: List[str], title: str, body: str,
                            data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send bulk push notifications
        
        Args:
            device_tokens: List of Firebase device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload (optional)
        
        Returns:
            Dictionary with bulk send status and results
        """
        try:
            # Validate inputs
            if not device_tokens or len(device_tokens) == 0:
                raise BadRequestError(
                    message="At least one device token is required",
                    verboseMessage="device_tokens list cannot be empty"
                )
            
            if not title or not body:
                raise BadRequestError(
                    message="Title and body are required",
                    verboseMessage="title and body fields must be provided"
                )
            
            logging.info(f"Sending bulk push notifications to {len(device_tokens)} devices")
            
            # Get Firebase provider
            provider = self.factory.get_provider("firebase")
            
            # Send bulk push notifications
            results = await provider.send_bulk(device_tokens, title, body, data)
            
            # Calculate statistics
            successful = sum(1 for r in results if r.get("status") == "sent")
            failed = len(results) - successful
            
            return {
                "success": failed == 0,
                "data": {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except BadRequestError:
            raise
        except Exception as e:
            logging.error(f"Bulk push notification send failed: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to send bulk push notifications",
                verboseMessage=str(e)
            )

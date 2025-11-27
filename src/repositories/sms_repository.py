"""
SMS Repository - Business logic for SMS operations
"""
from datetime import datetime
from typing import List, Dict, Any
from src.services.sms_service import SMSServiceFactory
from src.utils.libs.logging import logging
from src.utils.helpers.errors import BadRequestError, ServiceUnavailableError


class SMSRepository:
    """Repository for SMS operations"""
    
    def __init__(self):
        self.factory = SMSServiceFactory()
    
    async def send_single_sms(self, phone_number: str, message: str, realm: str) -> Dict[str, Any]:
        """
        Send a single SMS message
        
        Args:
            phone_number: Recipient's phone number
            message: Message content
            realm: SMS provider type (local, psi, thirdparty)
        
        Returns:
            Dictionary with send status
        """
        try:
            # Validate inputs
            if not phone_number or not message:
                raise BadRequestError(
                    message="Phone number and message are required",
                    verboseMessage="Both phone_number and message fields must be provided"
                )
            
            if not realm:
                raise BadRequestError(
                    message="SMS provider realm is required",
                    verboseMessage="Realm field must be one of: local, psi, thirdparty"
                )
            
            logging.info(f"Sending single SMS to {phone_number} via {realm}")
            provider = self.factory.get_provider(realm)
            result = await provider.send(phone_number, message)
            
            return {
                "success": result.get("status") == "sent",
                "data": result
            }
            
        except BadRequestError:
            raise
        except ValueError as ve:
            raise BadRequestError(
                message=f"Invalid SMS provider: {realm}",
                verboseMessage=str(ve)
            )
        except Exception as e:
            logging.error(f"SMS send failed: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to send SMS",
                verboseMessage=str(e)
            )
    
    async def send_bulk_sms(self, phone_numbers: List[str], message: str, realm: str) -> Dict[str, Any]:
        """
        Send bulk SMS messages
        
        Args:
            phone_numbers: List of recipient phone numbers
            message: Message content
            realm: SMS provider type (local, psi, thirdparty)
        
        Returns:
            Dictionary with bulk send status and results
        """
        try:
            # Validate inputs
            if not phone_numbers or len(phone_numbers) == 0:
                raise BadRequestError(
                    message="At least one phone number is required",
                    verboseMessage="Recipients list cannot be empty"
                )
            
            if not message:
                raise BadRequestError(
                    message="Message content is required",
                    verboseMessage="Message field cannot be empty"
                )
            
            if not realm:
                raise BadRequestError(
                    message="SMS provider realm is required",
                    verboseMessage="Realm field must be one of: local, psi, thirdparty"
                )
            
            
            # Get appropriate provider based on realm
            provider = self.factory.get_provider(realm)
            results = await provider.send_bulk(phone_numbers, message)
            
            # Calculate statistics
            successful = sum(1 for r in results if r.get("status") == "sent")
            failed = len(results) - successful
            logging.info(f"Sending bulk SMS to {len(phone_numbers)} recipients via {realm}")
            
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
        except ValueError as ve:
            raise BadRequestError(
                message=f"Invalid SMS provider: {realm}",
                verboseMessage=str(ve)
            )
        except Exception as e:
            logging.error(f"Bulk SMS send failed: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to send bulk SMS",
                verboseMessage=str(e)
            )

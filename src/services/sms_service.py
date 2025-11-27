"""
SMS Service - Core implementation for different SMS providers
"""
from abc import ABC, abstractmethod
from datetime import datetime
import uuid
from src.utils.libs.logging import logging


class BaseSMSProvider(ABC):
    """Abstract base class for SMS providers"""
    
    @abstractmethod
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS to a single recipient"""
        pass
    
    @abstractmethod
    async def send_bulk(self, phone_numbers: list, message: str) -> list:
        """Send SMS to multiple recipients"""
        pass


class LocalSMSProvider(BaseSMSProvider):
    """Local SMS Provider Implementation"""
    
    def __init__(self):
        self.provider_name = "LOCAL"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via local provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via LOCAL provider to {phone_number}")
            
            # TODO: Implement actual local SMS provider integration
            # This is where you would call your local SMS API
            
            return {
                "phone_number": phone_number,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"Local SMS send failed: {str(e)}")
            return {
                "phone_number": phone_number,
                "status": "failed",
                "error": str(e),
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_bulk(self, phone_numbers: list, message: str) -> list:
        """Send bulk SMS via local provider"""
        results = []
        for phone_number in phone_numbers:
            result = await self.send(phone_number, message)
            results.append(result)
        return results


class PSISMSProvider(BaseSMSProvider):
    """PSI SMS Provider Implementation"""
    
    def __init__(self):
        self.provider_name = "PSI"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via PSI provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via PSI provider to {phone_number}")
            
            # TODO: Implement actual PSI SMS provider integration
            # This is where you would call PSI SMS API with their credentials
            
            return {
                "phone_number": phone_number,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"PSI SMS send failed: {str(e)}")
            return {
                "phone_number": phone_number,
                "status": "failed",
                "error": str(e),
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_bulk(self, phone_numbers: list, message: str) -> list:
        """Send bulk SMS via PSI provider"""
        results = []
        for phone_number in phone_numbers:
            result = await self.send(phone_number, message)
            results.append(result)
        return results


class ThirdpartySMSProvider(BaseSMSProvider):
    """Third-party SMS Provider Implementation (e.g., Twilio, AWS SNS)"""
    
    def __init__(self):
        self.provider_name = "THIRDPARTY"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via third-party provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via THIRDPARTY provider to {phone_number}")
            
            # TODO: Implement actual third-party SMS integration
            # Examples: Twilio, AWS SNS, Firebase, etc.
            
            return {
                "phone_number": phone_number,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"Third-party SMS send failed: {str(e)}")
            return {
                "phone_number": phone_number,
                "status": "failed",
                "error": str(e),
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_bulk(self, phone_numbers: list, message: str) -> list:
        """Send bulk SMS via third-party provider"""
        results = []
        for phone_number in phone_numbers:
            result = await self.send(phone_number, message)
            results.append(result)
        return results


class SMSServiceFactory:
    """Factory class to get the appropriate SMS provider"""
    
    _providers = {
        "local": LocalSMSProvider,
        "psi": PSISMSProvider,
        "thirdparty": ThirdpartySMSProvider
    }
    
    @classmethod
    def get_provider(cls, provider_type: str) -> BaseSMSProvider:
        """Get SMS provider instance based on type"""
        provider_type = provider_type.lower()
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown SMS provider: {provider_type}")
        
        return cls._providers[provider_type]()

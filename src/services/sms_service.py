"""
SMS Service - Core implementation for different SMS providers
"""
from abc import ABC, abstractmethod
from datetime import datetime
import uuid, asyncio, httpx, aiosmtplib
from src.utils.libs.logging import logging

async def send_sms(url, payload, headers, method:str = "POST"):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

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


class ExternalSMSProvider(BaseSMSProvider):
    """External SMS Provider Implementation"""
    
    def __init__(self):
        self.provider_name = "EXTERNAL"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via External provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via External provider to {phone_number}")
            
            url = f"http://89.107.58.138:88/util/4552.sms"
            headers = {
                "Content-Type": "application/json", 
                "x-token": "NJC4E567-E7DA-4429-8451-9381E0CP",
                "cpid": 33
            }
            payload = {
                "SrcAddr": "4552",
                "DestAddr": phone_number,
                "ServiceID": "643",
                "Message": f"mycaller: {message}",
                "msgtype": "FLASH",
                "LinkID": datetime.utcnow().isoformat()
            }
            resp = await send_sms(url, payload, headers)
            logging.info(f"Sending SMS via External provider response {resp}")
            return {
                "phone_number": phone_number,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"External SMS send failed: {str(e)}")
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


class LocalSMSProvider(BaseSMSProvider):
    """Local SMS Provider Implementation"""
    
    def __init__(self):
        self.provider_name = "SMPP"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via local provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via LOCAL provider to {phone_number}")
            
            url = f"https://smsgateway.iyconsoft.com/send/?username=admin&password=admin&to={phone_number}&text={message}&coding=0&from=4800&smsc=smsc01&mclass=0"
            headers = {}
            # headers = {"Content-Type": "application/json"}
            resp = await send_sms(url, {}, headers, "GET")
            logging.info(f"Sending SMS via SMPP provider response {resp}")
            return {
                "phone_number": phone_number,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"SMPP SMS send failed: {str(e)}")
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
        self.provider_name = "PISI"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via PSI provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via PSI provider to {phone_number}")
            
            url = "https://api.pisimobile.com/api/SendSMS"
            headers = {"Content-Type": "application/json"}
            payload = {
                "MSISDN": f"{phone_number}",
                "ServiceID": "1409",
                "Text": message,
                "TokenID": "",
                "TransactionID": datetime.utcnow().isoformat()
            }
            resp = await send_sms(
                url = url,
                payload = payload,
                headers = headers
            )
            logging.info(f"Sending SMS via PSI provider response {resp}")
            return {
                "phone_number": "phone_number",
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


class CORPORATESMSProvider(BaseSMSProvider):
    """Cooperate SMS Provider Implementation (e.g., Twilio, AWS SNS)"""
    
    def __init__(self):
        self.provider_name = "CORPORATE"
    
    async def send(self, phone_number: str, message: str) -> dict:
        """Send SMS via third-party provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending SMS via THIRDPARTY provider to {phone_number}")
            
            url = f"http://108.181.156.128:8800/?phonenumber={phone_number}&text={message}&sender=4800&user=MTN&password=MTN&DCS=10"
            logging.info(f"Sending SMS via {self.provider_name} provider with url {url}")
            headers = {}
            resp = await send_sms(url, {}, headers, "GET")
            logging.info(f"Sending SMS via LOCAL provider response {resp}")
            
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
        "smpp": LocalSMSProvider,
        "pisi": PSISMSProvider,
        "coroperate": CORPORATESMSProvider,
        "external": ExternalSMSProvider
    }
    
    @classmethod
    def get_provider(cls, provider_type: str) -> BaseSMSProvider:
        """Get SMS provider instance based on type"""
        provider_type = provider_type.lower()
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown SMS provider: {provider_type}")
        
        return cls._providers[provider_type]()

from abc import ABC, abstractmethod
from datetime import datetime
import uuid, asyncio, httpx, aiosmtplib
from email.message import EmailMessage
from src.core.config import (settings, logging)
from src.utils import (EmailLib)
from .erp_service import ERPService


class BaseEmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    async def send(self, to_email: str, subject: str, body: str, html_body: str = None, template_id: int = None) -> dict:
        """Send email to a single recipient"""
        pass
    
    @abstractmethod
    async def send_bulk(self, recipients: list, subject: str, body: str, html_body: str = None) -> list:
        """Send email to multiple recipients"""
        pass


class SMTPEmailProvider(BaseEmailProvider):

    def __init__(self):
        self.provider_name = "SMTP"
        self.smtp_host = settings.mail_server
        self.smtp_port = settings.mail_port
        self.smtp_user = settings.mail_username
        self.smtp_password = settings.mail_password
        self.from_email = f"{settings.mail_from_name} <{settings.mail_sender}>"
    
    async def send(self, to_email: str, subject: str, body: str, html_body: str = None) -> dict:
        """Send email via SMTP provider"""
        try:
            message_id = f"<{uuid.uuid4()}@{self.from_email.split('@')[-1]}>"
            msg = EmailMessage()
            msg.add_header("X-Priority", "1")
            msg.add_header("Importance", "high")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg["Message-ID"] = message_id
            if html_body:
                html_content = await EmailLib.get_template('', 'index')
                html_body = html_content.replace('{{body}}', html_body)
                msg.set_content(body or "")
                msg.add_alternative(html_body, subtype="html")
            else:
                msg.set_content(body or "")
                
            send_kwargs = {
                "hostname": self.smtp_host,
                "port": self.smtp_port,
                "timeout": 30,
            }
            if self.smtp_user:
                send_kwargs["username"] = self.smtp_user
                send_kwargs["password"] = self.smtp_password or None
                
            start_tls = self.smtp_port in (587, 25)
            await aiosmtplib.send(msg, start_tls=start_tls, **send_kwargs)

            return {
                "to_email": to_email,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"SMTP email send failed: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def send_bulk(self, recipients: list, subject: str, body: str, html_body: str = None) -> list:
        """Send bulk emails via SMTP provider"""
        sem = asyncio.Semaphore(50)
        async def _send_with_sem(recipient: str):
            async with sem:
                return await self.send(recipient, subject, body, html_body)

        tasks = [asyncio.create_task(_send_with_sem(r)) for r in recipients]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results


class ERPEmailProvider(BaseEmailProvider):
    """ERP Email Provider Implementation"""
    
    def __init__(self):
        self.provider_name = "ERP"
        self.from_email = f"{settings.mail_from_name} <{settings.mail_sender}>"
        self.erp = ERPService()
    
    async def send(self, to_email: str, subject: str, body: str, html_body: str = None, template_id: str = None) -> dict:
        """Send email via ERP provider"""
        try:
            message_id = f"<{uuid.uuid4()}@{self.from_email.split('@')[-1]}>"

            if template_id is not None:
                template = await self.erp.send_request("mail.template", "read", [template_id])
            
            email_id = await self.erp.send_request("mail.mail", "create", [{
                "email_to": to_email,
                "subject": subject,
                "email_from": self.from_email,
                "body_html": html_body if html_body is not None else body
            }])
            resp = await self.erp.send_request("mail.mail", "send", email_id )
                
            return {
                "to_email": to_email,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error creating mail: {e.response.status_code} - {e.response.text}")
            raise

        except Exception as e:
            logging.error(f"ERP email send failed: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def send_bulk(self, recipients: list, subject: str, body: str, html_body: str = None) -> list:
        """Send bulk emails via ERP provider"""
        results = []
        for recipient in recipients:
            result = await self.send(recipient, subject, body, html_body)
            results.append(result)
        return results


class EmailServiceFactory:
    _providers = {
        "smtp": SMTPEmailProvider,
        "erp": ERPEmailProvider
    }
    
    @classmethod
    def get_provider(cls, provider_type: str) -> BaseEmailProvider:
        provider_type = provider_type.lower()
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown email provider: {provider_type}")
        
        return cls._providers[provider_type]()

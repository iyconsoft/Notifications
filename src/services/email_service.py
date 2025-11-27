from abc import ABC, abstractmethod
from datetime import datetime
import uuid, asyncio, httpx, aiosmtplib
from email.message import EmailMessage
from src.core.config import settings, logging
from src.utils import (EmailLib)


class BaseEmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    async def send(self, to_email: str, subject: str, body: str, html_body: str = None) -> dict:
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
        sem = asyncio.Semaphore(int(os.getenv("EMAIL_CONCURRENCY", "10")))
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
        self.erp_host = os.getenv("ERP_API_URL", "")
        self.erp_api_key = os.getenv("ERP_API_KEY", "")
    
    async def send(self, to_email: str, subject: str, body: str, html_body: str = None) -> dict:
        """Send email via ERP provider"""
        try:
            message_id = str(uuid.uuid4())
            logging.info(f"Sending email via ERP to {to_email}")
            # If ERP endpoint not configured, error out
            if not self.erp_host:
                raise RuntimeError("ERP API URL not configured")

            payload = {
                "to": to_email,
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "message_id": message_id,
            }
            headers = {"Content-Type": "application/json"}
            if self.erp_api_key:
                headers["Authorization"] = f"Bearer {self.erp_api_key}"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(self.erp_host, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json() if resp.content else {}

            return {
                "to_email": to_email,
                "message_id": message_id,
                "status": "sent",
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat(),
                "erp_response": data
            }
        except Exception as e:
            logging.error(f"ERP email send failed: {str(e)}")
            return {
                "to_email": to_email,
                "status": "failed",
                "error": str(e),
                "provider": self.provider_name,
                "timestamp": datetime.utcnow().isoformat()
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

from email.message import EmailMessage
from http.client import HTTPException
from pydantic import BaseModel
from typing import List
from aiosmtplib import send
from src.core.config import settings, os

class EmailLib():

    async def get_template(folder: str, name: str):
        try:
            file_path = os.path.join(f"templates/{folder}", f"{name}.html")
            with open(file_path, 'r') as file:
                html_content = file.read()
                return html_content
        except Exception as e:
            raise Exception(str(e))


    async def send_email(subject, recipient_email: str, body: str):
        try :
            html_content = await EmailLib.get_template('', 'index')
            html_body = html_content.replace('{{body}}', body)
            message = EmailMessage()
            message["From"] = f"{settings.mail_from_name} <{settings.mail_sender}>"
            message["Reply-To"] = settings.mail_sender
            message["To"] = recipient_email
            message["Subject"] = subject
            message.set_payload(html_body, charset='utf-8')  # Directly set the HTML body
            message.add_alternative(html_body, subtype='html')  # Add HTML alternative
            message.add_header("X-Priority", "1")
            message.add_header("Importance", "high")

            return await send(
                message=message,
                sender=settings.mail_sender,
                hostname=settings.mail_server,
                port=settings.mail_port,
                username=settings.mail_username,
                password=settings.mail_password,
                use_tls=settings.mail_tls, 
                validate_certs=settings.validate_certs,
                start_tls=settings.mail_ssl
            )
        except Exception as e:
            raise Exception(str(e))
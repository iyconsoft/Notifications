from email.message import EmailMessage
from http.client import HTTPException
import os
from pydantic import BaseModel
from typing import List
from aiosmtplib import send

mail_secret = os.getenv("SECRET_KEY")


class EmailSchema(BaseModel):
    email: List[str] = []

class EmailLib():


    async def get_template(folder: str, name: str):
        try:
            file_path = os.path.join(f"templates/{folder}", f"{name}.html")
            with open(file_path, 'r') as file:
                html_content = file.read()
                return html_content
        except Exception as e:
            print(e)
            raise Exception(str(e))


    async def send_email(subject, recipient_email: str, body: str):
        try :
            html_content = await EmailLib.get_template('', 'index')
            html_body = html_content.replace('{{body}}', body)
            message = EmailMessage()
            message["From"] = f"{os.getenv('MAIL_FROM_NAME')} <{os.getenv('MAIL_SENDER')}>"
            message["Reply-To"] = os.getenv('MAIL_SENDER')
            message["To"] = recipient_email
            message["Subject"] = subject
            message.set_payload(html_body, charset='utf-8')  # Directly set the HTML body
            message.add_alternative(html_body, subtype='html')  # Add HTML alternative
            message.add_header("X-Priority", "1")
            message.add_header("Importance", "high")

            return await send(
                message=message,
                sender=os.getenv("MAIL_SENDER"),
                hostname=os.getenv("MAIL_SERVER"),
                port=os.getenv("MAIL_PORT"),
                username=os.getenv("MAIL_USERNAME"),
                password=os.getenv("MAIL_PASSWORD"),
                use_tls=False, 
                validate_certs=True,
                start_tls=True
            )
        except Exception as e:
            print(e)
            raise Exception(str(e))
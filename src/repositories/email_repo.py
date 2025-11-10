from fastapi.responses import JSONResponse
from sqlalchemy import select
from src.core import settings, db
from src.utils import build_success_response, build_error_response
from src.utils.libs import EmailLib
from src.schemas import IMail

class EmailRepository:

    async def send_emails(info: IMail):
        for email in info.emails:
        return build_success_response( message="Bulk emails sent successfully" )


    async def subscribe_email(info: dict):
        try:            
            return {
                "message": 'email subscribed'
            }
        except Exception as e:
            return JSONResponse( status_code = 500, content = { "error": str(e) })


    async def email_notification(info: IMail):
        try:           
            return {
                "message": 'email sent'
            }
        except Exception as e:
            return JSONResponse( status_code = 500, content = { "error": str(e) })

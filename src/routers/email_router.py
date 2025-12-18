from fastapi import APIRouter, status, BackgroundTasks, Request, Depends, Header
from typing import Optional
from src.schemas import (
    EmailSingleRequest, EmailBulkRequest, EmailResponse,
    BulkNotificationResponse
)
from src.repositories import (EmailRepository)
from src.services import (eventrouter_handler)
from src.utils.helpers import (build_success_response, build_error_response, BaseError)
from src.core import (logging, settings)

router = APIRouter(tags=["Email Notifications"])
email_repo = EmailRepository()

            
@router.post(
    "/email/send",
    status_code=status.HTTP_200_OK,
    summary="Send Single Email",
    description="Send a single email using specified provider (smtp or erp)"
)
async def send_single_email(request: EmailSingleRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            email_repo.send_single_email, 
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            provider=request.provider
        )    
        return build_success_response(
            message="Email operation in progress",
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Unexpected error in email send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )
            
@router.post(
    "/email/webhook",
    status_code=status.HTTP_200_OK,
    summary="Webhook Email Alert",
    description="Send email alerts via webhook (e.g., from Grafana)"
)
async def webhook_email(request: Request, background_tasks: BackgroundTasks, x_grafana_token: Optional[str] = Header(None)):
    try:
        if x_grafana_token != settings.grafana_webhook_token:
            return build_error_response(
                message="Invalid Grafana webhook token",
                status=status.HTTP_401_UNAUTHORIZED
            )

        payload = await request.json()
        background_tasks.add_task(
            email_repo.grafana_alert, 
            info=payload
        )    
        return build_success_response(
            message="Webhook email operation in progress",
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Unexpected error in email send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


@router.post(
    "/email/bulk",
    status_code=status.HTTP_200_OK,
    summary="Send Bulk Emails",
    description="Send emails to multiple recipients using specified provider"
)
async def send_bulk_emails(request: EmailBulkRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            email_repo.send_bulk_emails, 
            recipients=request.recipients,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            provider=request.provider
        )    
        
        return build_success_response(
            message="Bulk emails operation in progress",
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Unexpected error in bulk email send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


eventrouter_handler.register_handler('send_email', send_single_email, settings.queue_name)
eventrouter_handler.register_handler('send_bulk_email', send_bulk_emails, settings.queue_name)
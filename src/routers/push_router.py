from fastapi import APIRouter, status
from src.schemas import (
    SMSSingleRequest, SMSBulkRequest, SMSResponse,
    EmailSingleRequest, EmailBulkRequest, EmailResponse,
    PushNotificationSingleRequest, PushNotificationBulkRequest, PushNotificationResponse,
    BulkNotificationResponse
)
# from src.repositories.sms_repository import SMSRepository
from src.repositories import (EmailRepository)
# from src.repositories.push_repository import PushNotificationRepository
from src.utils.helpers import (build_success_response, build_error_response, BaseError)
from src.core import (logging)

# Create router
router = APIRouter(tags=["Notifications"])

# Initialize repositories
# sms_repo = SMSRepository()
email_repo = EmailRepository()
# push_repo = PushNotificationRepository()

@router.post(
    "/sms/send",
    status_code=status.HTTP_200_OK,
    summary="Send Single SMS",
    description="Send a single SMS message to a recipient using specified provider (local, psi, or thirdparty)"
)
async def send_single_sms(request: SMSSingleRequest):
    """
    Send a single SMS message
    
    **Parameters:**
    - `phone_number`: Recipient's phone number
    - `message`: SMS message content
    - `realm`: SMS provider type (local, psi, thirdparty)
    
    **Response:** SMS sent status with message ID
    """
    try:
        logging.info(f"SMS send endpoint called for {request.phone_number}")
        
        result = await sms_repo.send_single_sms(
            phone_number=request.phone_number,
            message=request.message,
            realm=request.realm
        )
        
        return build_success_response(
            message="SMS sent successfully",
            status=status.HTTP_200_OK,
            data=result["data"]
        )
    except BaseError as e:
        logging.error(f"SMS send error: {e.message}")
        return build_error_response(
            message=e.message,
            status=e.httpCode,
            data={"error_type": e.errorType, "verbose_message": e.verboseMessage}
        )
    except Exception as e:
        logging.error(f"Unexpected error in SMS send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


@router.post(
    "/sms/send-bulk",
    status_code=status.HTTP_200_OK,
    summary="Send Bulk SMS",
    description="Send SMS messages to multiple recipients using specified provider"
)
async def send_bulk_sms(request: SMSBulkRequest):
    """
    Send bulk SMS messages
    
    **Parameters:**
    - `recipients`: List of phone numbers
    - `message`: SMS message content
    - `realm`: SMS provider type (local, psi, thirdparty)
    
    **Response:** Bulk SMS send status with results and statistics
    """
    try:
        logging.info(f"Bulk SMS send endpoint called for {len(request.recipients)} recipients")
        
        result = await sms_repo.send_bulk_sms(
            phone_numbers=request.recipients,
            message=request.message,
            realm=request.realm
        )
        
        return build_success_response(
            message="Bulk SMS sent successfully",
            status=status.HTTP_200_OK,
            data=result["data"]
        )
    except BaseError as e:
        logging.error(f"Bulk SMS send error: {e.message}")
        return build_error_response(
            message=e.message,
            status=e.httpCode,
            data={"error_type": e.errorType, "verbose_message": e.verboseMessage}
        )
    except Exception as e:
        logging.error(f"Unexpected error in bulk SMS send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


# ==================== EMAIL ENDPOINTS ====================

@router.post(
    "/email/send",
    status_code=status.HTTP_200_OK,
    summary="Send Single Email",
    description="Send a single email using specified provider (smtp or erp)"
)
async def send_single_email(request: EmailSingleRequest):
    """
    Send a single email
    
    **Parameters:**
    - `to_email`: Recipient's email address
    - `subject`: Email subject
    - `body`: Email body (plain text)
    - `html_body`: Email body (HTML format, optional)
    - `provider`: Email provider type (smtp, erp)
    
    **Response:** Email sent status with message ID
    """
    try:
        logging.info(f"Email send endpoint called for {request.to_email}")
        
        result = await email_repo.send_single_email(
            to_email=request.to_email,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            provider=request.provider
        )
        
        return build_success_response(
            message="Email sent successfully",
            status=status.HTTP_200_OK,
            data=result["data"]
        )
    except BaseError as e:
        logging.error(f"Email send error: {e.message}")
        return build_error_response(
            message=e.message,
            status=e.httpCode,
            data={"error_type": e.errorType, "verbose_message": e.verboseMessage}
        )
    except Exception as e:
        logging.error(f"Unexpected error in email send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


@router.post(
    "/email/send-bulk",
    status_code=status.HTTP_200_OK,
    summary="Send Bulk Emails",
    description="Send emails to multiple recipients using specified provider"
)
async def send_bulk_emails(request: EmailBulkRequest):
    """
    Send bulk emails
    
    **Parameters:**
    - `recipients`: List of email addresses
    - `subject`: Email subject
    - `body`: Email body (plain text)
    - `html_body`: Email body (HTML format, optional)
    - `provider`: Email provider type (smtp, erp)
    
    **Response:** Bulk email send status with results and statistics
    """
    try:
        logging.info(f"Bulk email send endpoint called for {len(request.recipients)} recipients")
        
        result = await email_repo.send_bulk_emails(
            recipients=request.recipients,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            provider=request.provider
        )
        
        return build_success_response(
            message="Bulk emails sent successfully",
            status=status.HTTP_200_OK,
            data=result["data"]
        )
    except BaseError as e:
        logging.error(f"Bulk email send error: {e.message}")
        return build_error_response(
            message=e.message,
            status=e.httpCode,
            data={"error_type": e.errorType, "verbose_message": e.verboseMessage}
        )
    except Exception as e:
        logging.error(f"Unexpected error in bulk email send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


# ==================== PUSH NOTIFICATION ENDPOINTS ====================

@router.post(
    "/push/send",
    status_code=status.HTTP_200_OK,
    summary="Send Single Push Notification",
    description="Send a single push notification via Firebase"
)
async def send_single_push(request: PushNotificationSingleRequest):
    """
    Send a single push notification
    
    **Parameters:**
    - `device_token`: Firebase device token
    - `title`: Notification title
    - `body`: Notification body
    - `data`: Additional data payload (optional)
    
    **Response:** Push notification sent status with message ID
    """
    try:
        logging.info(f"Push notification send endpoint called for device: {request.device_token}")
        
        result = await push_repo.send_single_push(
            device_token=request.device_token,
            title=request.title,
            body=request.body,
            data=request.data
        )
        
        return build_success_response(
            message="Push notification sent successfully",
            status=status.HTTP_200_OK,
            data=result["data"]
        )
    except BaseError as e:
        logging.error(f"Push notification send error: {e.message}")
        return build_error_response(
            message=e.message,
            status=e.httpCode,
            data={"error_type": e.errorType, "verbose_message": e.verboseMessage}
        )
    except Exception as e:
        logging.error(f"Unexpected error in push notification send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


@router.post(
    "/push/send-bulk",
    status_code=status.HTTP_200_OK,
    summary="Send Bulk Push Notifications",
    description="Send push notifications to multiple devices via Firebase"
)
async def send_bulk_push(request: PushNotificationBulkRequest):
    """
    Send bulk push notifications
    
    **Parameters:**
    - `device_tokens`: List of Firebase device tokens
    - `title`: Notification title
    - `body`: Notification body
    - `data`: Additional data payload (optional)
    
    **Response:** Bulk push notification send status with results and statistics
    """
    try:
        logging.info(f"Bulk push notification send endpoint called for {len(request.device_tokens)} devices")
        
        result = await push_repo.send_bulk_push(
            device_tokens=request.device_tokens,
            title=request.title,
            body=request.body,
            data=request.data
        )
        
        return build_success_response(
            message="Bulk push notifications sent successfully",
            status=status.HTTP_200_OK,
            data=result["data"]
        )
    except BaseError as e:
        logging.error(f"Bulk push notification send error: {e.message}")
        return build_error_response(
            message=e.message,
            status=e.httpCode,
            data={"error_type": e.errorType, "verbose_message": e.verboseMessage}
        )
    except Exception as e:
        logging.error(f"Unexpected error in bulk push notification send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )

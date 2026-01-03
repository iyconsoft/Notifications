from fastapi import APIRouter, status, BackgroundTasks, Request, Depends
from src.schemas import (
    SMSSingleRequest, SMSBulkRequest, SMSResponse,
    BulkNotificationResponse
)
from src.repositories import (SMSRepository)
from src.services import (eventrouter_handler)
from src.utils.helpers import (build_success_response, build_error_response, BaseError)
from src.core import (logging, settings)

router = APIRouter(tags=["Sms Notifications"])
sms_repo = SMSRepository()

@router.post(
    "/sms/send",
    status_code=status.HTTP_200_OK,
    summary="Send Single SMS",
    description="Send a single SMS message to a recipient using specified provider (local, psi, or thirdparty)"
)
async def send_single_sms(request: SMSSingleRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            sms_repo.send_single_sms,
            phone_number=request.phone_number,
            message=request.message,
            realm=request.realm
        )
        
        return build_success_response(
            message="SMS sending operation in progress",
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Unexpected error in SMS send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


@router.post(
    "/sms/bulk",
    status_code=status.HTTP_200_OK,
    summary="Send Bulk SMS",
    description="Send SMS messages to multiple recipients using specified provider"
)
async def send_bulk_sms(request: SMSBulkRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(
            sms_repo.send_bulk_sms,
            phone_numbers=request.recipients,
            message=request.message,
            realm=request.realm
        )
        
        return build_success_response(
            message="Bulk SMS operation in progress",
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error(f"Unexpected error in bulk SMS send: {str(e)}")
        return build_error_response(
            message="An unexpected error occurred",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={"error": str(e)}
        )


async def process_sms_message(payload: dict):
    """Process sms message from queue"""
    try:
        sms_type = payload.get("type")
        sms_data = payload.get("payload", {})
        is_bulk = payload.get("isBulk", False)

        await sms_repo.send_bulk_sms(
            **sms_data
        ) if is_bulk else await sms_repo.send_single_sms(**sms_data)

        return {"status": "success"}
    except Exception as e:
        logging.error(f"failed to process sms message {str(e)}")
        return {"status": "failed", "error": str(e)}


eventrouter_handler.register_handler(
    message_type='sms', 
    callback=process_sms_message,
    queue_name=settings.queue_name
)



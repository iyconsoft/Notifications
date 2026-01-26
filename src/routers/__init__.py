from src.routers.app_router import appRouter, APIRouter
from src.routers.email_router import router as email_router, process_email_message
from src.routers.sms_router import router as sms_router, process_sms_message


api_router = APIRouter()
api_router.include_router(email_router, responses={404: {"description": "Not found"}})
api_router.include_router(sms_router, responses={404: {"description": "Not found"}})
api_router.include_router(appRouter, responses={404: {"description": "Not found"}})


from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from fastapi.responses import Response
from src.utils import build_success_response, build_error_response, check_db, check_app
from src.core.config import logging


appRouter = APIRouter(tags=["Iyconsoft Notifications"])

@appRouter.get("/")
async def home():
    return build_success_response(message="IFitness sync app is running ✅")

@appRouter.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@appRouter.get("/health", summary="Health Check Endpoint")
async def health_check(request: Request):
    health_status = {
        "status": "healthy",
        "services": {
            "notification_db": status.HTTP_200_OK if await check_db(request.app.state.dbengine) else status.HTTP_503_SERVICE_UNAVAILABLE,
            "event_handler": {
                # "rabbitmq_connected": worker.connection is not None,
                # "is_consuming": worker.is_consuming
            }
        }
    }
    
    # If any service is unhealthy, change overall status
    if any(service is True for service in health_status["services"].values()):
    # if any(service["status"] != "healthy" for service in health_status["services"].values()):
        health_status["status"] = "degraded"
        return build_error_response(
            "degraded", status.HTTP_207_MULTI_STATUS, health_status
        )
    
    return build_success_response(
        "acknowledged", status.HTTP_200_OK, health_status
    )

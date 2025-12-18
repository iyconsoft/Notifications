from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from fastapi.responses import Response
from src.utils import build_success_response, build_error_response, check_rabbitmq, check_db, check_url_health
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
        "rabbitmq": await check_rabbitmq(request.app.state.rabbit_connection),
        # "db": await check_db(db.session),
        "erp": await check_url_health("https://backoffice.kreador.io/jsonrpc"),
        "firebase": await check_url_health("https://aide-financial.firebaseio.com"),
    }
    
    if any(service is True for service in health_status.values()):
    # if any(service["status"] != "healthy" for service in health_status["services"].values()):
        return build_error_response(
            "degraded", status.HTTP_207_MULTI_STATUS, health_status
        )
    
    return build_success_response(
        "healthy", status.HTTP_200_OK, health_status
    )

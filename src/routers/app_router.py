from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from fastapi.responses import Response
from src.utils import build_success_response, build_error_response, check_rabbitmq, check_db, check_url_health
from src.core import logging, settings, engine, db
import asyncio


appRouter = APIRouter(tags=["Iyconsoft Notifications"])

@appRouter.get("/")
async def home():
    return build_success_response(message=settings.app_description)

@appRouter.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@appRouter.get("/health", summary="Health Check Endpoint")
async def health_check(request: Request):
    rabbitmq, _db, smpp, pisi, coroperate, erp = await asyncio.gather(
        check_rabbitmq(request.app.state.rabbit_connection),
        check_db(engine, db.session),
        check_url_health("https://smsgateway.iyconsoft.com/status?password=admin"),
        check_url_health("https://api.pisimobile.com/"),
        check_url_health("http://108.181.156.128:8800"),
        check_url_health("https://erp.iyconsoft.com/web/health")
    )
    health_status = {
        "rabbitmq": rabbitmq,
        "db": _db,
        "erp": erp,
        "smpp": smpp,
        # "pisi": pisi,
        # "coroperate": coroperate
    }
    
    if any(service["status"] != "healthy" for service in health_status.values()):
        return build_error_response(
            "degraded", status.HTTP_207_MULTI_STATUS, health_status
        )
    
    return build_success_response(
        "healthy", status.HTTP_200_OK, health_status
    )

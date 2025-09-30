from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.utils.helpers.error_messages import *
from src.utils.helpers.error_types import *
from src.utils.helpers.errors import BaseError
from src.utils.libs.logging import logging
from src.utils.helpers.api_responses import build_error_response

async def base_error_handler(request: Request, exc: BaseError):
    return build_error_response(
        message=exc.message,
        status=exc.httpCode,
        data={
            "verbose_message": exc.verboseMessage,
            "error_type": exc.errorType,
        }
    )


async def not_found_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/flasgger_static"):
        return JSONResponse(status_code=204, content="")

    logging.error("Route not found: %s", request.url.path)
    return build_error_response(
        notFoundErrorMessage, statusCodes['404'], 
        data={
            "verbose_message": f"Error: {exc}",
            "error_type": errorTypes['NOT_FOUND_ERROR'],
        })


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return build_error_response(
        badRequestErrorMessage, statusCodes['400'], 
        data={
            "verbose_message": f"Error: {exc}",
            "error_type": errorTypes['VALIDATION_FAILED'],
        })

    
# async def global_exception_handler(request: Request, exc: Exception):
#     return build_error_response(internalServerErrorMessage, statusCodes['500'])


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logging.error(f"{internalServerErrorMessage}: {exc}", exc_info=False)
        return build_error_response(
            internalServerErrorMessage, statusCodes['500'], 
            data={
                "verbose_message": f"Error: {exc}",
                "error_type": errorTypes['INTERNAL_SERVER_ERROR'],
            })

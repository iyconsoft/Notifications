import os, ssl
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware

from src.utils.libs import SecurityHeadersMiddleware
from src.utils.helpers.errors import *
from src.utils.helpers.exception_handler import *
from src.utils.helpers.rate_limiting import RateLimiter

from .dbconfig import (
    SQLALCHEMY_DATABASE_URL,
    engine_args,
)


def add_app_middlewares(app: FastAPI):
    origins = os.getenv("APP_ORIGINS")
    RateLimiter()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(GZipMiddleware, minimum_size=10)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=origins)
    app.add_middleware(SecurityHeadersMiddleware, csp=True)
    app.add_middleware(
        SQLAlchemyMiddleware, db_url=SQLALCHEMY_DATABASE_URL, engine_args=engine_args
    )

    @app.middleware("http")
    async def exceptions_middleware(request: Request, call_next):
        return await catch_exceptions_middleware(request, call_next)

    if os.getenv("SSL") is True:
        app.add_middleware(HTTPSRedirectMiddleware)

    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context


async def add_exception_middleware(app: FastAPI):
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(StarletteHTTPException, not_found_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # app.add_exception_handler(Exception, global_exception_handler)
    
import os, ssl
from fastapi import FastAPI
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi_async_sqlalchemy import SQLAlchemyMiddleware

from src.utils import *
from .config import ( settings )
from src.core.dbconfig import (
    SQLALCHEMY_DATABASE_URL,
    engine_args,
)

middlewares = [
    Middleware(ExceptionMiddleware), 
    Middleware(GZipMiddleware, minimum_size=10), 
    Middleware(TrustedHostMiddleware, allowed_hosts=settings.app_origins), 
    Middleware(SecurityHeadersMiddleware, csp=True), 
    Middleware(CORSMiddleware, allow_origins=settings.app_origins, allow_methods=settings.app_origins, allow_headers=settings.app_origins, allow_credentials=True),
    Middleware(SQLAlchemyMiddleware, db_url=SQLALCHEMY_DATABASE_URL, engine_args=engine_args)
]

def add_app_middlewares(app: FastAPI):
    @app.middleware("http")
    async def ip_block(request: Request, call_next):
            return await block_ips(request, call_next)

    @app.middleware("http")
    async def exceptions_middleware(request: Request, call_next):
        return await catch_exceptions_middleware(request, call_next)

async def add_exception_middleware(app: FastAPI):
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(StarletteHTTPException, not_found_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # app.add_exception_handler(Exception, global_exception_handler)
    
if os.getenv("SSL") is True:
    app.add_middleware(HTTPSRedirectMiddleware)

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context
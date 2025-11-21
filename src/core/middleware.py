import os, ssl
from fastapi import Request, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.config import ( settings )
from src.core.dbconfig import (
    SQLALCHEMY_DATABASE_URL,
    engine_args,
)
from src.utils.helpers import (
    RateLimiter, ExceptionMiddleware
)
from src.utils.libs import *

middlewares = [
    Middleware(ExceptionMiddleware), 
    Middleware(GZipMiddleware, minimum_size=10), 
    Middleware(TrustedHostMiddleware, allowed_hosts=settings.app_origins), 
    Middleware(SecurityHeadersMiddleware, csp=True), 
    Middleware(CORSMiddleware, allow_origins=settings.app_origins, allow_methods=settings.app_origins, allow_headers=settings.app_origins, allow_credentials=True),
    Middleware(SQLAlchemyMiddleware, db_url=SQLALCHEMY_DATABASE_URL, engine_args=engine_args),
    Middleware(SentryAsgiMiddleware)
]



def add_app_middlewares(app: FastAPI):
    RateLimiter()
    Instrumentator().instrument(app).expose(app)
    
    if os.getenv("SSL") is True:
        app.add_middleware(HTTPSRedirectMiddleware)

    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context

    # if settings.debug is False:
    #     sentry_init(settings.debug, settings.sentry_dns)
        
    # @app.middleware("http")
    # async def ip_block(request: Request, call_next):
    #     return await block_ips(request, call_next)


async def add_exception_middleware(app: FastAPI):
    app.add_exception_handler(BaseError, base_error_handler)
    app.add_exception_handler(StarletteHTTPException, not_found_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

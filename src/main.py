from contextlib import asynccontextmanager
from src.routers import APIRouter, appRouter, email_router, sms_router
from src.services import eventrouter_handler
from src.core import (
    FastAPI, add_app_middlewares, add_exception_middleware, settings, asyncio, middlewares, logging
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.gather(
        eventrouter_handler.connect_rabbitmq(app),
        add_exception_middleware(app),
        return_exceptions=True
    )
    
    yield
    if hasattr(app.state, 'worker_task'):
        app.state.worker_task.cancel()

    if hasattr(app.state, 'app.state.eventrouter_handler'):
        await eventrouter_handler.stop_consuming()
        await app.state.rabbit_connection.close()

app: FastAPI = FastAPI(
    debug = settings.debug,
    version = settings.app_version,
    title = settings.app_name,
    description = settings.app_description,
    root_path = settings.app_root,
    middleware = middlewares,
    port = settings.port,
    redoc_url = None,
    lifespan = lifespan,
    servers=[{"url": f"/{settings.app_root}", "description": f"{settings.app_name} endpoints"}]
)

add_app_middlewares(app)
app.include_router(appRouter, responses={404: {"description": "Not found"}})
app.include_router(email_router, responses={404: {"description": "Not found"}})
app.include_router(sms_router, responses={404: {"description": "Not found"}})



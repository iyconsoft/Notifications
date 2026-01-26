from contextlib import asynccontextmanager
from src.routers import api_router
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
    await asyncio.gather(
        # eventrouter_handler.setup_queue_consumer("mycaller_queue", app),
        eventrouter_handler.register_handler('email', process_email_message, settings.queue_name ),
        # eventrouter_handler.register_handler('push', process_push_message, settings.queue_name ),
        eventrouter_handler.register_handler('sms', process_sms_message, settings.queue_name ),
        return_exceptions=True
    )
    
    yield
    if hasattr(app.state, 'worker_task'):
        app.state.worker_task.cancel()

    if hasattr(app.state, 'app.state.eventrouter_handler'):
        await eventrouter_handler.stop_all()
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
app.include_router(api_router)
await eventrouter_handler.setup_consumers(app)

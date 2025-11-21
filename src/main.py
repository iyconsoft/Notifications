from contextlib import asynccontextmanager
from src.routers import APIRouter, appRouter
from src.services import EventHandler_Service
from aio_pika import connect_robust
from src.core import (
    FastAPI, init_db, add_app_middlewares, add_exception_middleware, settings, asyncio, middlewares, logging
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try: 
        _, connection = await asyncio.gather(
            init_db(app),
            connect_robust(settings.rabbitmq_url),
            add_exception_middleware(app),
            return_exceptions=True
        )
        await EventHandler_Service(app, connection)

    except Exception as ex:
        logging.error(f"Lifespan startup failed: {ex}")
        raise
    yield
    try:
        if hasattr(app.state, 'dbengine'):
            await app.state.dbengine.dispose()
        if hasattr(app.state, 'worker_task'):
            app.state.worker_task.cancel()
        # Shutdown logic
        await app.state.rabbit_connection.close()
    except asyncio.CancelledError:
        pass

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
    servers=[{"url": "/api", "description": f"{settings.app_name} endpoints"}]
)

add_app_middlewares(app)
app.include_router(appRouter, responses={404: {"description": "Not found"}})

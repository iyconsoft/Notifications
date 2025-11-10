from contextlib import asynccontextmanager
from src.routers import APIRouter, appRouter
from src.core import (
    FastAPI, init_db, add_app_middlewares, add_exception_middleware, settings, asyncio, middlewares, logging
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try: 
        await asyncio.gather(
            init_db(app),
            add_exception_middleware(app),
        )
    except Exception as ex:
        logging.error(f"Lifespan startup failed: {ex}")
        raise
    yield
    try:
        if hasattr(app.state, 'dbengine'):
            await app.state.dbengine.dispose()
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

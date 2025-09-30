from contextlib import asynccontextmanager
from src.core import (
    FastAPI, init_db, add_app_middlewares, add_exception_middleware, settings
)
from src.utils.libs.worker import close_worker, start_worker, handle_message, RabbitMQ
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.gather(
        init_db(app),
        add_exception_middleware(app),
        # start_worker(handle_message, rabbitmq),
    )
    yield

app: FastAPI = FastAPI(
    debug = settings.debug,
    version = settings.app_version,
    title = settings.app_name,
    description = settings.app_description,
    root_path = settings.app_root,
    redoc_url = None,
    lifespan=lifespan
)
rabbitmq = RabbitMQ()
add_app_middlewares(app)

@app.on_event("shutdown")
async def shutdown_event():
    await close_worker(rabbitmq)

@app.get("")
async def root():
    # This will be caught by the middleware
    raise Exception("Something went wrong")

# app.include_router(
#     referral_router,
#     tags=["Referrals"],
#     responses={404: {"description": "Not found"}},
# )


# app.include_router(
#     reward_router,
#     prefix="/rewards",
#     tags=["Rewards"],
#     responses={404: {"description": "Not found"}},
# )

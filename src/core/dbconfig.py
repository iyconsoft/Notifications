from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import baseDir, os, logging


Base: DeclarativeMeta = declarative_base()
mode = bool(os.getenv("DEBUG"))
uri = os.getenv("SQLALCHEMY_DATABASE_URI")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
server = os.getenv("DB_SERVER")
port = os.getenv("DB_PORT")
dbname = os.getenv("DB_NAME")
dialect = os.getenv("DB_DIALECT")

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///" + os.path.join( baseDir, f"{dbname}.db" ) if dialect == "sqlite" else f"{uri}://{username}:{password}@{server}:{port}/{dbname}"
engine_args: dict = (
    {
        "pool_pre_ping": True,  # feature will normally emit SQL equivalent to “SELECT 1” each time a connection is checked out from the pool
        "pool_size": 10,  # number of connections to keep open at a time
        "max_overflow": 5,  # number of connections to allow to be opened above pool_size
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }
    if mode is False or dialect != "sqlite"
    else {}
)

async def init_db(app: FastAPI):
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.engine = engine
    app.state.SessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )



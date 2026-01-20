from fastapi import FastAPI
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import baseDir, os, logging, settings


Base: DeclarativeMeta = declarative_base()
mode = settings.debug
uri = settings.sqlalchemy_database_uri
username = settings.db_username
password = settings.db_password
server = settings.db_server
port = settings.db_port
dbname = settings.db_name
dialect = settings.db_dialect
dbname = settings.db_name if settings.db_dialect == 'sqlite' else settings.db_external_name
print(dialect)

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///" + os.path.join( baseDir, f"{dbname}.db" ) if dialect == "sqlite" else f"{uri}://{username}:{password}@{server}:{port}/{dbname}"
engine_args: dict = (
    {
        "pool_pre_ping": True,  # feature will normally emit SQL equivalent to “SELECT 1” each time a connection is checked out from the pool
        "pool_size": 10,  # number of connections to keep open at a time
        "max_overflow": 5,  # number of connections to allow to be opened above pool_size
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }
    if dialect != "sqlite"
    else {
        "echo": False,
        "pool_pre_ping": True,
    }
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.debug,
    future=True,
)

async def init_db():
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
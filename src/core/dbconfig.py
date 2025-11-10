from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import baseDir, os, logging, settings


Base: DeclarativeMeta = declarative_base()
mode = settings.debug
uri = settings.sqlalchemy_database_uri
dbname = settings.db_name

SQLALCHEMY_DATABASE_URL = f"{uri}:///" + os.path.join( baseDir, f"{dbname}.db" )
engine_args: dict = ({})

async def init_db(app: FastAPI):
    try:
        app.state.dbengine = create_async_engine(
            SQLALCHEMY_DATABASE_URL, 
            echo=False, 
            connect_args={"check_same_thread": False}, 
            future=True
        )
        app.state.dbsession = async_sessionmaker(
            bind=app.state.dbengine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        async with app.state.dbengine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logging.info("✅ Sqlite db initialized successfully")
    except Exception as e:
        logging.error(str(e))




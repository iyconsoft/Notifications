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





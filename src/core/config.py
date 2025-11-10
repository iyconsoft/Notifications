import os, logging, asyncio
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.libs import log_handler, logger

logging.basicConfig(level=logging.DEBUG, handlers=[log_handler])
baseDir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(f"{baseDir}/.conf")


# Settings class using Pydantic
class AppSettings(BaseSettings):
    debug: bool
    is_demo: bool = True
    app_name: str
    app_description: str
    app_origins: list[str]
    app_root: str
    port: int
    app_version: str
    secret_key: str
    db_name: str
    sqlalchemy_database_uri: str
    remotedb_url: str

    qbwc_soap_url: str = "http://schemas.xmlsoap.org/soap/envelope/"
    qbwc_url: str = "http://developer.intuit.com/"
    qbwc_username: str = "ifitness_qbwc_user"
    qbwc_password: str = "ifitness_qbwc_pass"
    qwbcmodules: list[str] = ["customers", "employees", "invoices", "gl_entries"]

    model_config = SettingsConfigDict(env_file=".conf") 


# # Instance to use across app
settings = AppSettings()



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
    mail_server: str
    mail_port: int
    mail_sender: int
    mail_username: str
    mail_password: str
    mail_from_name: str
    mail_tls: bool
    mail_ssl: bool
    use_credentials: bool
    validate_certs: bool

    model_config = SettingsConfigDict(env_file=".conf") 


# # Instance to use across app
settings = AppSettings()



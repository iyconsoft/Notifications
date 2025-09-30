import os, logging
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.libs import log_handler


logging.basicConfig(level=logging.DEBUG, handlers=[log_handler])
baseDir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(f"{baseDir}/.conf")


# Settings class using Pydantic
class AppSettings(BaseSettings):
    debug: bool
    app_name: str
    app_description: str
    app_root: str
    app_version: str
    redis_url: str
    rabbitmq_url: str

    model_config = SettingsConfigDict(env_file=".conf") 


# # Instance to use across app
settings = AppSettings()



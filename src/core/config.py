import os, logging, asyncio
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.utils.libs import log_handler, logger

logging.basicConfig(level=logging.DEBUG, handlers=[log_handler])
baseDir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(f"{baseDir}/.conf")


# Settings class using Pydantic
class AppSettings(BaseSettings):
    debug: bool = True
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

    rabbitmq_url: str = "amqp://admin:admin123@devserver.iyconsoft.com:5672"
    queue_name: str = "notification_queue"

    mail_server: str
    mail_port: int
    mail_sender: str
    mail_username: str
    mail_password: str
    mail_from_name: str
    mail_tls: bool = True
    mail_ssl: bool = False
    use_credentials: bool = True
    validate_certs: bool = True

    odoo_url: str = "https://backoffice.kreador.io/jsonrpc"
    odoo_headers: dict = {
        'Content-Type': 'application/json'
    }
    odoo_payload: dict = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute",
            "args": [
                "developer_backoffice_db",
                2,
                "admin"
            ]
        }
    }

    model_config = SettingsConfigDict(env_file=".conf") 


# # Instance to use across app
settings = AppSettings()



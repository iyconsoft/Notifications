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

    rabbitmq_url: str
    queue_name: str

    keycloak_realm: str
    keycloak_server_url: str
    keycloak_client_id: str
    keycloak_client_secret: str

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

    sentry_dns: str = "https://952e53885dce39d9c6dc481ddbad407f@o4504234422632448.ingest.us.sentry.io/4507927449698304"

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



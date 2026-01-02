import logging
from colorlog import ColoredFormatter


# Logging setup
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "INFO": "green",
        "WARNING": "yellow",
        "DEBUG": "cyan",
        "ERROR": "red",
        "CRITICAL": "red",
        "RESET": "purple"
    },
)

logging.getLogger("aio_pika").setLevel(logging.ERROR)
logging.getLogger("aiormq").setLevel(logging.ERROR)
logging.getLogger("aiosqlite").setLevel(logging.ERROR)
logging.getLogger("aiomysql").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
log_handler.setFormatter(formatter)

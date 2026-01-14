import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# agent setup
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DOCS_FOLDER = "docs/"
FILE_EXTENSIONS = (".pdf", ".txt", ".md")
MODEL = "x-ai/grok-4.1-fast"
INPUT_PRICE = 0.2
OUTPUT_PRICE = 0.5

# telegram bot setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DAILY_QUERY_LIMIT = 10
TELEGRAM_BOT_NAME = "@ponaehaliam_bot"

# logging setup
LOGS_DIR = Path("logs")
LOG_FILE = LOGS_DIR / "bot.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format=LOG_FORMAT,
    level=LOG_LEVEL,
    force=True,
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        ),
    ],
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

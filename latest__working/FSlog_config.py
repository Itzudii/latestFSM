import logging
from logging.handlers import TimedRotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger():
    logger = logging.getLogger("FS")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(threadName)s | %(filename)s:%(lineno)d | %(message)s"
    )

    # 🔹 Daily rotating debug log
    debug_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "debug.log"),
        when="midnight",
        interval=1,
        backupCount=14,     # keep last 14 days
        encoding="utf-8"
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)

    # 🔹 Daily rotating error log
    error_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "error.log"),
        when="midnight",
        interval=1,
        backupCount=30,     # keep last 30 days
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(debug_handler)
        logger.addHandler(error_handler)

    return logger

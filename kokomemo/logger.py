from .config import config
import logging
from logging import StreamHandler, FileHandler

logger = logging.getLogger(config.app_name)
logger.setLevel(config.loglevel)

asyncio_logger = logging.getLogger("asyncio")

formatter = logging.Formatter(
    fmt="%(levelname)s | %(asctime)s | "
    "%(funcName)s (%(filename)s:%(lineno)d): %(message)s"
)

stream_handler = StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
asyncio_logger.addHandler(stream_handler)

if config.logfile:
    file_handler = FileHandler(config.logfile, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

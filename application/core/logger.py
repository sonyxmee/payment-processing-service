import logging
import sys

from application.core.config import settings


def setup_logging(name: str = settings.app_title):
    """Настройка логгера для приложения"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


main_logger: logging.Logger = setup_logging()
outbox_logger: logging.Logger = setup_logging('outbox')

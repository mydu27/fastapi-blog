import sys
from loguru import logger
from app.core.config import settings


# log初始化方法
def init_logger():
    logger.remove(handler_id=None)
    if settings.LOG_ENABLED and settings.LOG_TO_CONSOLE:
        logger.add(sys.stderr, level=settings.LEVEL)
    if settings.LOG_ENABLED and settings.LOG_TO_FILE:
        logger.add(settings.LOG_PATH,
                   rotation=settings.ROTATION,
                   level=settings.LEVEL,
                   enqueue=True,
                   compression=settings.COMPRESSION,
                   retention=settings.RETENTION)
    return

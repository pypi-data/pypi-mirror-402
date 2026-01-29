import logging
import sys
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """
    Create or retrieve a configured logger.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Logger already configured
        return logger

    # Inherit root level by default so CLI/user config controls verbosity.
    logger.setLevel(logging.NOTSET)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.NOTSET)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def set_log_level(level: Any) -> None:
    """
    Set the log level for root + existing module loggers.
    """
    if isinstance(level, str):
        resolved = getattr(logging, level.upper(), logging.INFO)
    else:
        resolved = int(level)

    logging.getLogger().setLevel(resolved)
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(resolved)
            for handler in logger.handlers:
                handler.setLevel(resolved)

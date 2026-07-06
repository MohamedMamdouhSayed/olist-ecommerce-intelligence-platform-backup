"""Centralized Python logging configuration for the platform."""

import logging
import logging.config

from configs.constants import DEFAULT_LOG_LEVEL, LOG_DATE_FORMAT, LOG_FORMAT
from configs.validators import validate_log_level


def configure_logging(log_level: str = DEFAULT_LOG_LEVEL) -> None:
    """Configure process-wide logging with a consistent enterprise format."""
    normalized_level = validate_log_level(log_level)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": LOG_FORMAT,
                    "datefmt": LOG_DATE_FORMAT,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": normalized_level,
                }
            },
            "root": {
                "handlers": ["console"],
                "level": normalized_level,
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module logger using the centralized logging configuration."""
    return logging.getLogger(name)


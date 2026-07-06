"""Reusable structured logger with console and rotating file handlers."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from observability.exceptions import LoggerConfigurationError
from observability.logging_config import (
    LoggingConfig,
    StructuredLogFormatter,
    normalize_log_level,
)


class Logger:
    """Factory and convenience wrapper for structured Python loggers."""

    def __init__(self, config: LoggingConfig) -> None:
        """Create a logger using the provided configuration."""
        self.config = config
        self._logger = logging.getLogger(config.logger_name)
        self._configure()

    @property
    def instance(self) -> logging.Logger:
        """Return the underlying Python logger."""
        return self._logger

    def _configure(self) -> None:
        """Configure handlers, formatter, and log level."""
        if not self.config.enable_console and not self.config.enable_file:
            raise LoggerConfigurationError("At least one logging handler must be enabled.")

        log_level = normalize_log_level(self.config.log_level)
        self._logger.setLevel(log_level)
        self._logger.propagate = False
        self._logger.handlers.clear()

        formatter = StructuredLogFormatter()

        if self.config.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        if self.config.enable_file:
            if self.config.log_file is None:
                raise LoggerConfigurationError("log_file is required when file logging is enabled.")

            log_file = Path(self.config.log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def bind(
        self,
        execution_id: str | None = None,
        pipeline_stage: str | None = None,
        **extra_fields: Any,
    ) -> logging.LoggerAdapter:
        """Return a logger adapter with structured context fields."""
        return logging.LoggerAdapter(
            self._logger,
            {
                "execution_id": execution_id,
                "pipeline_stage": pipeline_stage,
                "extra_fields": extra_fields,
            },
        )


def get_logger(
    name: str,
    log_level: str = "INFO",
    log_file: Path | None = None,
    enable_console: bool = True,
    enable_file: bool = False,
) -> logging.Logger:
    """Return a configured structured logger."""
    return Logger(
        LoggingConfig(
            logger_name=name,
            log_level=log_level,
            log_file=log_file,
            enable_console=enable_console,
            enable_file=enable_file,
        )
    ).instance


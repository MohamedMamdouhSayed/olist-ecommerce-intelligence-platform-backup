"""Logging configuration models and structured formatters."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_LOG_FORMAT_FIELDS = (
    "timestamp",
    "level",
    "module",
    "function",
    "execution_id",
    "pipeline_stage",
    "message",
    "duration_ms",
)


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for reusable loggers."""

    logger_name: str
    log_level: str = "INFO"
    log_file: Path | None = None
    enable_console: bool = True
    enable_file: bool = False
    max_bytes: int = 10_485_760
    backup_count: int = 5


class StructuredLogFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON log line with standard observability fields."""
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "execution_id": getattr(record, "execution_id", None),
            "pipeline_stage": getattr(record, "pipeline_stage", None),
            "message": record.getMessage(),
            "duration_ms": getattr(record, "duration_ms", None),
        }

        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            payload.update(extra_fields)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, ensure_ascii=True)


def normalize_log_level(log_level: str) -> int:
    """Normalize a text logging level to a Python logging constant."""
    normalized = log_level.strip().upper()
    if normalized not in logging._nameToLevel:
        raise ValueError(f"Invalid log level: {log_level}")

    return logging._nameToLevel[normalized]


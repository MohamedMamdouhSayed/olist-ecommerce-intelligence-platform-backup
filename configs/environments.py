"""Environment definitions for the platform configuration layer."""

from enum import Enum

from configs.constants import DEFAULT_ENVIRONMENT


class Environment(str, Enum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


def normalize_environment(value: str | None) -> Environment:
    """Normalize a raw environment value into a supported environment enum."""
    normalized = (value or DEFAULT_ENVIRONMENT).strip().lower()
    return Environment(normalized)

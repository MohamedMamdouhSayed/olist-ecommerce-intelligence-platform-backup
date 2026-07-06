"""Project-wide constants for configuration management."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "configs"
DEFAULT_ENV_FILE = CONFIG_DIR / ".env"

DEFAULT_ENVIRONMENT = "development"
VALID_ENVIRONMENTS = {"development", "testing", "production"}

DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOCAL_SOURCE_SYSTEM = "olist"
AZURE_KEY_VAULT_SECRET_PREFIX = "olist"


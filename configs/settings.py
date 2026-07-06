"""Backwards-compatible settings facade for platform configuration.

New code should import ``get_settings`` from ``configs.config``. This module
continues to expose the original uppercase variables so existing components can
adopt the enterprise configuration package incrementally.
"""

from configs.config import PlatformSettings, get_settings
from configs.constants import DEFAULT_ENV_FILE as ENV_FILE
from configs.constants import PROJECT_ROOT
from configs.logging_config import configure_logging, get_logger


settings: PlatformSettings = get_settings()

configure_logging(settings.log_level)
logger = get_logger(__name__)

# Project metadata
PROJECT_NAME = settings.project_name
ENVIRONMENT = settings.environment.value
LOG_LEVEL = settings.log_level

# Local data lake paths
DATA_PATH = settings.data_path
BRONZE_PATH = settings.bronze_path
SILVER_PATH = settings.silver_path
GOLD_PATH = settings.gold_path

# Kafka starter configuration. This module does not create Kafka connections.
KAFKA_BOOTSTRAP_SERVER = settings.kafka_bootstrap_server
KAFKA_TOPIC_ORDERS = settings.kafka_topic_orders

# Spark starter configuration. This module does not create Spark sessions.
SPARK_APP_NAME = settings.spark_app_name

# Future Azure Key Vault configuration.
USE_AZURE_KEY_VAULT = settings.use_azure_key_vault
AZURE_KEY_VAULT_URL = settings.azure_key_vault_url


if __name__ == "__main__":
    logger.info("Loaded settings for %s", PROJECT_NAME)
    logger.info("Environment: %s", ENVIRONMENT)
    logger.info("Raw data path: %s", DATA_PATH)
    logger.info("Bronze path: %s", BRONZE_PATH)
    logger.info("Silver path: %s", SILVER_PATH)
    logger.info("Gold path: %s", GOLD_PATH)

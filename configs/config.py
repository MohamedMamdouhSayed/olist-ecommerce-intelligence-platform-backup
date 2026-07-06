"""Enterprise configuration model for the Olist data platform."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from configs.constants import DEFAULT_ENV_FILE, DEFAULT_ENVIRONMENT, DEFAULT_LOG_LEVEL
from configs.environments import Environment
from configs.validators import (
    ensure_directory,
    validate_log_level,
    validate_required_string,
)


class PlatformSettings(BaseSettings):
    """Typed and validated platform settings loaded from local `.env` files.

    The model centralizes configuration for all platform layers while avoiding
    any runtime side effects such as Kafka connections, Spark sessions, or cloud
    client initialization.
    """

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    environment: Environment = Field(default=DEFAULT_ENVIRONMENT, alias="ENVIRONMENT")
    project_name: str = Field(default="olist-platform", alias="PROJECT_NAME")
    log_level: str = Field(default=DEFAULT_LOG_LEVEL, alias="LOG_LEVEL")

    data_path: Path = Field(default=Path("data/raw"), alias="DATA_PATH")
    bronze_path: Path = Field(default=Path("data/bronze"), alias="BRONZE_PATH")
    silver_path: Path = Field(default=Path("data/silver"), alias="SILVER_PATH")
    gold_path: Path = Field(default=Path("data/gold"), alias="GOLD_PATH")

    kafka_bootstrap_server: str = Field(default="localhost:9092", alias="KAFKA_BOOTSTRAP_SERVER")
    kafka_topic_orders: str = Field(default="olist.orders", alias="KAFKA_TOPIC_ORDERS")
    kafka_topic_customers: str = Field(default="olist.customers", alias="KAFKA_TOPIC_CUSTOMERS")
    kafka_topic_products: str = Field(default="olist.products", alias="KAFKA_TOPIC_PRODUCTS")
    kafka_topic_sellers: str = Field(default="olist.sellers", alias="KAFKA_TOPIC_SELLERS")
    kafka_topic_order_items: str = Field(default="olist.order_items", alias="KAFKA_TOPIC_ORDER_ITEMS")
    kafka_topic_order_payments: str = Field(default="olist.order_payments", alias="KAFKA_TOPIC_ORDER_PAYMENTS")
    kafka_topic_order_reviews: str = Field(default="olist.order_reviews", alias="KAFKA_TOPIC_ORDER_REVIEWS")
    kafka_topic_geolocation: str = Field(default="olist.geolocation", alias="KAFKA_TOPIC_GEOLOCATION")
    kafka_topic_category_translation: str = Field(default="olist.category_translation", alias="KAFKA_TOPIC_CATEGORY_TRANSLATION")

    spark_app_name: str = Field(default="olist-spark", alias="SPARK_APP_NAME")

    azure_key_vault_url: str | None = Field(default=None, alias="AZURE_KEY_VAULT_URL")
    use_azure_key_vault: bool = Field(default=False, alias="USE_AZURE_KEY_VAULT")

    @field_validator(
        "project_name",
        "kafka_bootstrap_server",
        "kafka_topic_orders",
        "kafka_topic_customers",
        "kafka_topic_products",
        "kafka_topic_sellers",
        "kafka_topic_order_items",
        "kafka_topic_order_payments",
        "kafka_topic_order_reviews",
        "kafka_topic_geolocation",
        "kafka_topic_category_translation",
        "spark_app_name",
    )
    @classmethod
    def required_strings(cls, value: str, info) -> str:
        """Ensure required string values are not blank."""
        return validate_required_string(value, info.field_name)

    @field_validator("log_level")
    @classmethod
    def valid_log_level(cls, value: str) -> str:
        """Validate and normalize the configured logging level."""
        return validate_log_level(value)

    @model_validator(mode="after")
    def validate_environment_rules(self) -> "PlatformSettings":
        """Apply cross-field validation for environment-specific rules."""
        if self.environment == Environment.PRODUCTION and self.log_level == "DEBUG":
            raise ValueError("Production LOG_LEVEL must not be DEBUG.")

        if self.use_azure_key_vault and not self.azure_key_vault_url:
            raise ValueError(
                "AZURE_KEY_VAULT_URL is required when USE_AZURE_KEY_VAULT=true."
            )

        self.data_path = ensure_directory(self.data_path)
        self.bronze_path = ensure_directory(self.bronze_path)
        self.silver_path = ensure_directory(self.silver_path)
        self.gold_path = ensure_directory(self.gold_path)

        return self

    @property
    def is_development(self) -> bool:
        """Return whether the active environment is development."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Return whether the active environment is testing."""
        return self.environment == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Return whether the active environment is production."""
        return self.environment == Environment.PRODUCTION


@lru_cache
def get_settings() -> PlatformSettings:
    """Return cached, validated platform settings."""
    return PlatformSettings()


"""Orders Kafka producer for the Olist raw orders dataset."""

from __future__ import annotations

from pathlib import Path

from configs.config import PlatformSettings, get_settings
from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class OrdersProducer(BaseProducer):
    """Publish valid Olist order records to the configured orders Kafka topic."""

    DEFAULT_SOURCE_PATH = Path("data/raw/olist_orders_dataset.csv")
    KEY_COLUMN = "order_id"
    REQUIRED_COLUMNS = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    REQUIRED_FIELDS = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
    ]

    def __init__(
        self,
        batch_size: int = 1_000,
        retry_count: int = 3,
        retry_backoff_seconds: float = 1.0,
        settings: PlatformSettings | None = None,
    ) -> None:
        """Initialize the orders producer using centralized platform settings."""
        platform_settings = settings or get_settings()
        super().__init__(
            topic=platform_settings.kafka_topic_orders,
            batch_size=batch_size,
            retry_count=retry_count,
            retry_backoff_seconds=retry_backoff_seconds,
            settings=platform_settings,
        )

    def publish_orders(
        self,
        csv_path: str | Path = DEFAULT_SOURCE_PATH,
    ) -> dict[str, int]:
        """Read, validate, and publish Olist orders to Kafka."""
        return self.publish_csv(
            csv_path=csv_path,
            validation_engine=self._build_validation_engine(),
            key_column=self.KEY_COLUMN,
        )

    def _build_validation_engine(self) -> ValidationEngine:
        """Build the validation engine for the Olist orders dataset."""
        engine = ValidationEngine()
        engine.register_validators(
            [
                SchemaValidator(required_columns=self.REQUIRED_COLUMNS),
                NullValidator(required_fields=self.REQUIRED_FIELDS),
            ]
        )
        return engine


def main() -> None:
    """Run the orders producer for the default raw orders dataset."""
    with OrdersProducer() as producer:
        producer.publish_orders()


if __name__ == "__main__":
    main()

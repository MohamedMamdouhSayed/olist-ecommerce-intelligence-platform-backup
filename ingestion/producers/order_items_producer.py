"""Order Items producer for ingesting order items data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class OrderItemsProducer(BaseProducer):
    """Producer for ingesting order items data to Kafka topic 'olist.order_items'."""

    def __init__(
        self,
        topic: str = "olist.order_items",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the order items producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_order_items(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send order item records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "order_id", 
                    "order_item_id", 
                    "product_id", 
                    "seller_id", 
                    "price", 
                    "freight_value"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "order_id", 
                    "product_id", 
                    "seller_id"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="order_id"
        )

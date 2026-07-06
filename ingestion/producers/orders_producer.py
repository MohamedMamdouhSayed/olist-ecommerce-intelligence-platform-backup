"""Orders producer for ingesting order data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class OrdersProducer(BaseProducer):
    """Producer for ingesting orders data to Kafka topic 'olist.orders'."""

    def __init__(
        self,
        topic: str = "olist.orders",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the orders producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_orders(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send order records to Kafka."""
        engine = ValidationEngine()
        
        # Register schema validator
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "order_id", 
                    "customer_id", 
                    "order_status", 
                    "order_purchase_timestamp"
                ]
            )
        )
        
        # Register null validator
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "order_id", 
                    "customer_id", 
                    "order_status"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="order_id"
        )

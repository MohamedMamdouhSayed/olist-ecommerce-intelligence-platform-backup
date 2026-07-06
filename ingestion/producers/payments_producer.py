"""Payments producer for ingesting payment data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class PaymentsProducer(BaseProducer):
    """Producer for ingesting payments data to Kafka topic 'olist.order_payments'."""

    def __init__(
        self,
        topic: str = "olist.order_payments",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the payments producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_payments(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send payment records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "order_id", 
                    "payment_sequential", 
                    "payment_type", 
                    "payment_installments", 
                    "payment_value"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "order_id", 
                    "payment_type"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="order_id"
        )

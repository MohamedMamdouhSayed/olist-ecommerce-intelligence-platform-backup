"""Sellers producer for ingesting seller data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class SellersProducer(BaseProducer):
    """Producer for ingesting sellers data to Kafka topic 'olist.sellers'."""

    def __init__(
        self,
        topic: str = "olist.sellers",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the sellers producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_sellers(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send seller records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "seller_id", 
                    "seller_zip_code_prefix", 
                    "seller_city", 
                    "seller_state"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "seller_id"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="seller_id"
        )

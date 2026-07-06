"""Products producer for ingesting product data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class ProductsProducer(BaseProducer):
    """Producer for ingesting products data to Kafka topic 'olist.products'."""

    def __init__(
        self,
        topic: str = "olist.products",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the products producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_products(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send product records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "product_id", 
                    "product_category_name"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "product_id"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="product_id"
        )

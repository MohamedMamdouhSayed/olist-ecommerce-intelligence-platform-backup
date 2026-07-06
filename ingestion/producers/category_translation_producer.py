"""Category Translation producer for ingesting category translation data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class CategoryTranslationProducer(BaseProducer):
    """Producer for ingesting category translation data to Kafka topic 'olist.category_translation'."""

    def __init__(
        self,
        topic: str = "olist.category_translation",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the category translation producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_translations(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send category translation records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "product_category_name", 
                    "product_category_name_english"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "product_category_name"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="product_category_name"
        )

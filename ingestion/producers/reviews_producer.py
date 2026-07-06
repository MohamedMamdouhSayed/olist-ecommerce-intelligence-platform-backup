"""Reviews producer for ingesting review data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class ReviewsProducer(BaseProducer):
    """Producer for ingesting reviews data to Kafka topic 'olist.order_reviews'."""

    def __init__(
        self,
        topic: str = "olist.order_reviews",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the reviews producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_reviews(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send review records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "review_id", 
                    "order_id", 
                    "review_score"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "review_id", 
                    "order_id"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="order_id"
        )

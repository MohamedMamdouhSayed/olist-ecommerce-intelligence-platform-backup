"""Geolocation producer for ingesting geolocation data to Kafka."""

from pathlib import Path
from typing import Optional

from ingestion.producers.base_producer import BaseProducer
from validation.nulls.null_validator import NullValidator
from validation.schema.schema_validator import SchemaValidator
from validation.validation_engine import ValidationEngine


class GeolocationProducer(BaseProducer):
    """Producer for ingesting geolocation data to Kafka topic 'olist.geolocation'."""

    def __init__(
        self,
        topic: str = "olist.geolocation",
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
    ):
        """Initialize the geolocation producer."""
        super().__init__(
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            batch_size=batch_size,
            retry_count=retry_count,
            producer_timeout=producer_timeout,
        )

    def send_geolocation(self, csv_path: str | Path) -> dict[str, int]:
        """Load, validate, and send geolocation records to Kafka."""
        engine = ValidationEngine()
        
        engine.register_validator(
            SchemaValidator(
                required_columns=[
                    "geolocation_zip_code_prefix", 
                    "geolocation_lat", 
                    "geolocation_lng", 
                    "geolocation_city", 
                    "geolocation_state"
                ]
            )
        )
        
        engine.register_validator(
            NullValidator(
                required_fields=[
                    "geolocation_zip_code_prefix"
                ]
            )
        )

        return self.ingest_from_csv(
            csv_path=csv_path,
            validation_engine=engine,
            key_column="geolocation_zip_code_prefix"
        )

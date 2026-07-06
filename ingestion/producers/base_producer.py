"""Enterprise Kafka producer with connection management, retry logic, and observability."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from configs.config import get_settings
from ingestion.readers.csv_reader import CSVReader
from observability.decorators import log_execution, measure_time, track_metrics
from observability.logger import get_logger
from observability.monitoring import get_global_monitoring_service
from validation.validation_engine import ValidationEngine
from validation.validation_result import ValidationStatus
from typing import Optional, Any, Callable

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError, KafkaTimeoutError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception
    KafkaTimeoutError = TimeoutError


import logging
logger = logging.getLogger(__name__)


class DeliveryReport:
    """Report of message delivery status."""

    def __init__(
        self,
        topic: str,
        partition: int,
        offset: int,
        key: Optional[str],
        value: bytes,
        timestamp: int,
        error: Optional[Exception] = None,
    ):
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.key = key
        self.value = value
        self.timestamp = timestamp
        self.error = error


class BaseProducer:
    """Enterprise Kafka producer with connection management, retry logic, and observability.

    Provides:
    - Connection Management
    - Retry Logic
    - Delivery Callback
    - JSON Serialization
    - Graceful Shutdown
    - Metrics
    - Logging
    """

    def __init__(
        self,
        topic: str,
        bootstrap_servers: Optional[str] = None,
        batch_size: int = 1000,
        retry_count: int = 3,
        producer_timeout: int = 30,
        linger_ms: int = 10,
        enable_idempotence: bool = True,
    ):
        """Initialize the base producer.

        Args:
            topic: Kafka topic to publish to
            bootstrap_servers: Kafka bootstrap servers (from config if not provided)
            batch_size: Number of records per batch
            retry_count: Number of retry attempts
            producer_timeout: Producer timeout in seconds
            linger_ms: Time to wait before sending batch (milliseconds)
            enable_idempotence: Enable idempotent producer
        """
        if not KAFKA_AVAILABLE:
            raise ImportError(
                "kafka-python package is required. Install it with: pip install kafka-python"
            )

        self.topic = topic
        self.settings = get_settings()
        self.bootstrap_servers = bootstrap_servers or self.settings.kafka_bootstrap_server
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.producer_timeout = producer_timeout
        self.linger_ms = linger_ms
        self.enable_idempotence = enable_idempotence

        self._producer: Optional[KafkaProducer] = None
        self._is_connected = False
        self._delivery_callback: Optional[Callable[[DeliveryReport], None]] = None

        # Initialize monitoring
        self.monitoring = get_global_monitoring_service()
        component_name = f"kafka_producer_{topic}"
        if not self.monitoring.is_registered(component_name):
            self.monitoring.register_component(
                name=component_name,
                component_type="kafka_producer",
                metadata={"topic": topic},
            )

        logger.info(
            f"BaseProducer initialized for topic: {topic} with bootstrap_servers: {self.bootstrap_servers}"
        )

    @log_execution
    @measure_time
    def connect(self) -> None:
        """Create a producer connection to Kafka cluster."""
        if self._is_connected:
            logger.warning("Producer already connected", topic=self.topic)
            return

        try:
            kafka_config = {
                "bootstrap_servers": self.bootstrap_servers,
                "batch_size": self.batch_size,
                "linger_ms": self.linger_ms,
                "acks": "all",
                "retries": self.retry_count,
                "max_in_flight_requests_per_connection": 5,
                "enable_idempotence": self.enable_idempotence,
                "request_timeout_ms": self.producer_timeout * 1000,
            }

            self._producer = KafkaProducer(**kafka_config)
            self._is_connected = True

            logger.info(
                f"Kafka producer connected successfully to {self.bootstrap_servers} for topic {self.topic}"
            )

            self.monitoring.record_success(
                f"kafka_producer_{self.topic}",
                f"connect_{datetime.utcnow().timestamp()}",
                duration_ms=0,
            )

        except Exception as e:
            self._is_connected = False
            logger.error(f"Failed to connect to Kafka for topic {self.topic}: {e}")
            self.monitoring.record_failure(
                f"kafka_producer_{self.topic}",
                f"connect_{datetime.utcnow().timestamp()}",
                duration_ms=0,
                error=e,
            )
            raise

    def _delivery_report_callback(
        self,
        error: Optional[KafkaError],
        record_metadata: Any,
    ) -> None:
        """Callback for message delivery reports."""
        if error:
            report = DeliveryReport(
                topic=self.topic,
                partition=-1,
                offset=-1,
                key=None,
                value=b"",
                timestamp=0,
                error=error,
            )

            logger.error(f"Message delivery failed for topic {self.topic}: {error}")

            if self._delivery_callback:
                self._delivery_callback(report)
        else:
            report = DeliveryReport(
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                key=None,
                value=b"",
                timestamp=record_metadata.timestamp,
            )

            logger.debug(
                "Message delivered successfully",
                topic=self.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
            )

            if self._delivery_callback:
                self._delivery_callback(report)

    def set_delivery_callback(self, callback: Callable[[DeliveryReport], None]) -> None:
        """Set the delivery callback function."""
        self._delivery_callback = callback

    @track_metrics(component_name="kafka_producer_send")
    def send(self, record: dict[str, Any], key: Optional[str] = None) -> bool:
        """Send a single record to Kafka with retry logic.

        Args:
            record: Record data to send
            key: Optional message key for partitioning

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._is_connected:
            logger.error(f"Producer not connected for topic {self.topic}")
            return False

        for attempt in range(self.retry_count):
            try:
                serialized_value = json.dumps(record, default=str).encode("utf-8")

                future = self._producer.send(
                    self.topic,
                    key=key.encode("utf-8") if key else None,
                    value=serialized_value,
                )

                future.add_callback(self._delivery_report_callback)
                future.add_errback(self._delivery_report_callback)

                logger.debug("Record sent to Kafka", topic=self.topic, key=key)
                return True

            except Exception as e:
                if attempt < self.retry_count - 1:
                    logger.warning(
                        "Send attempt failed, retrying",
                        topic=self.topic,
                        attempt=attempt + 1,
                        total_retries=self.retry_count,
                        error=str(e),
                    )
                    time.sleep(1 * (attempt + 1))
                else:
                    logger.error(f"Failed to send record after retries for topic {self.topic}: {e}")
                    return False

        return False

    @log_execution
    @measure_time
    def flush(self, timeout: Optional[float] = None) -> bool:
        """Flush pending messages to Kafka.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            True if flush completed successfully
        """
        if not self._is_connected:
            return False

        try:
            flush_timeout = timeout if timeout is not None else self.producer_timeout
            self._producer.flush(timeout=flush_timeout)

            logger.debug("Producer flushed successfully", topic=self.topic)
            return True

        except Exception as e:
            logger.error(f"Failed to flush producer for topic {self.topic}: {e}")
            return False

    @log_execution
    @measure_time
    def disconnect(self) -> None:
        """Close the producer connection and release resources."""
        if self._producer:
            try:
                self.flush()
                self._producer.close()
                self._is_connected = False

                logger.info("Producer disconnected gracefully", topic=self.topic)

            except Exception as e:
                logger.error(f"Error closing producer for topic {self.topic}: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._is_connected

    @log_execution
    @measure_time
    def ingest_from_csv(
        self,
        csv_path: str | Path,
        validation_engine: Optional[ValidationEngine] = None,
        key_column: Optional[str] = None,
    ) -> dict[str, int]:
        """Load, validate, and send records from a CSV file.

        Args:
            csv_path: Path to the CSV source file
            validation_engine: Optional validation engine with registered validators
            key_column: Optional column name to use as Kafka message key

        Returns:
            Dictionary with processing statistics
        """
        stats = {"total_processed": 0, "total_published": 0, "total_failed": 0}
        csv_reader = CSVReader()
        
        logger.info(f"Starting CSV ingestion for topic {self.topic} from path {csv_path}")
        self.connect()

        try:
            # Use a dummy dataframe if file reading fails during testing
            try:
                df = csv_reader.load_dataframe(csv_path)
            except Exception as e:
                logger.error(f"Failed to load CSV: {e}")
                return stats
            
            # Run validation if engine is provided
            invalid_indices = set()
            validation_errors: dict[int, list[str]] = {}
            
            if validation_engine:
                report = validation_engine.run(df)
                for check in report.failed_checks:
                    if check.failed_indices:
                        for idx in check.failed_indices:
                            invalid_indices.add(idx)
                            if idx not in validation_errors:
                                validation_errors[idx] = []
                            validation_errors[idx].append(f"{check.validation_name}: {check.message}")

            # Process rows
            for idx, row in df.iterrows():
                stats["total_processed"] += 1
                record = row.to_dict()
                
                if idx in invalid_indices:
                    stats["total_failed"] += 1
                    self._handle_failed_record(
                        record, 
                        "Validation failed", 
                        validation_errors.get(idx, ["Unknown validation error"])
                    )
                    continue

                key = str(record.get(key_column)) if key_column else None
                if self.send(record, key=key):
                    stats["total_published"] += 1
                else:
                    stats["total_failed"] += 1
                    self._handle_failed_record(record, "Kafka send failed")

            self.flush()
            
        except Exception as e:
            logger.error("Ingestion failed", error=str(e))
            raise

        logger.info(f"Ingestion completed for topic {self.topic}: {stats}")
        return stats

    def _handle_failed_record(
        self,
        record: dict[str, Any],
        error_message: str,
        errors: Optional[list[str]] = None,
    ) -> None:
        """Handle failed records by persisting them to disk."""
        failed_dir = Path(self.settings.data_path) / "failed_records" / self.topic
        failed_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        file_path = failed_dir / f"failed_{timestamp_str}.json"

        failed_payload = {
            "record": record,
            "error": error_message,
            "validation_errors": errors,
            "topic": self.topic,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(failed_payload, f, indent=2, default=str)

        logger.warning("Failed record persisted", path=str(file_path))


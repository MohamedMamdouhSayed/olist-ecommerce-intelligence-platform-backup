"""Reusable Kafka producer base for JSON batch publishing."""

from __future__ import annotations

import json
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from types import FrameType
from typing import Any, Callable

import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

from configs.config import PlatformSettings, get_settings
from observability.logger import get_logger
from observability.monitoring import MonitoringService, get_global_monitoring_service
from validation.reports.quality_report import QualityReport
from validation.validation_engine import ValidationEngine


logger = get_logger(__name__)
LOCAL_KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
CONFLUENT_CLOUD_BOOTSTRAP_SERVER = "pkc-921jm.us-east-2.aws.confluent.cloud:9092"


@dataclass(frozen=True)
class DeliveryReport:
    """Delivery result emitted by the Kafka producer callbacks."""

    topic: str
    partition: int | None
    offset: int | None
    key: str | None
    error: str | None = None


class BaseProducer:
    """Base Kafka producer with batching, retries, callbacks, and shutdown."""

    def __init__(
        self,
        topic: str,
        batch_size: int = 1_000,
        retry_count: int = 5,
        retry_backoff_seconds: float = 1.0,
        request_timeout_ms: int = 30_000,
        linger_ms: int = 10,
        settings: PlatformSettings | None = None,
        monitoring_service: MonitoringService | None = None,
    ) -> None:
        """Initialize shared producer settings from the platform configuration."""
        self.settings = settings or get_settings()
        self.topic = topic
        self.batch_size = batch_size
        self.retry_count = retry_count
        self.retry_backoff_seconds = retry_backoff_seconds
        self.request_timeout_ms = request_timeout_ms
        self.linger_ms = linger_ms
        self.bootstrap_servers = self._bootstrap_servers()
        self.monitoring = monitoring_service or get_global_monitoring_service()
        self.component_name = f"kafka_producer_{self.topic}"
        self.shutdown_event = Event()
        self.producer: KafkaProducer | None = None
        self.delivery_callback: Callable[[DeliveryReport], None] | None = None

        self.monitoring.register_component(
            name=self.component_name,
            component_type="kafka_producer",
            metadata={"topic": self.topic},
        )
        self._register_shutdown_handlers()

        logger.info(
            "Kafka producer initialized",
            extra={
                "pipeline_stage": "ingestion",
                "extra_fields": {
                    "topic": self.topic,
                    "batch_size": self.batch_size,
                    "bootstrap_servers": self.bootstrap_servers,
                },
            },
        )

    def connect(self) -> None:
        """Create the kafka-python producer client."""
        if self.producer is not None:
            return

        try:
            self.producer = KafkaProducer(**self._producer_config())
            logger.info(
                "Kafka producer connected",
                extra={
                    "pipeline_stage": "ingestion",
                    "extra_fields": {"topic": self.topic},
                },
            )
        except Exception as exc:
            self.monitoring.record_failure(
                self.component_name,
                execution_id="producer_connect",
                duration_ms=0.0,
                error=exc,
            )
            logger.exception(
                "Kafka producer connection failed",
                extra={
                    "pipeline_stage": "ingestion",
                    "extra_fields": {"topic": self.topic},
                },
            )
            raise

    def close(self) -> None:
        """Flush pending messages and close the producer gracefully."""
        if self.producer is None:
            return

        try:
            self.producer.flush(timeout=self.request_timeout_ms / 1_000)
            self.producer.close(timeout=self.request_timeout_ms / 1_000)
            logger.info(
                "Kafka producer closed",
                extra={
                    "pipeline_stage": "ingestion",
                    "extra_fields": {"topic": self.topic},
                },
            )
        finally:
            self.producer = None

    def set_delivery_callback(
        self,
        callback: Callable[[DeliveryReport], None],
    ) -> None:
        """Register a callback invoked after each delivery callback event."""
        self.delivery_callback = callback

    def publish_dataframe(
        self,
        dataframe: pd.DataFrame,
        validation_engine: ValidationEngine,
        key_column: str | None = None,
    ) -> dict[str, int]:
        """Validate and publish a DataFrame in configured batches."""
        stats = self._empty_stats()
        self.connect()

        for start in range(0, len(dataframe), self.batch_size):
            if self.shutdown_event.is_set():
                break

            batch = dataframe.iloc[start : start + self.batch_size]
            batch_stats = self._publish_batch(
                batch=batch,
                validation_engine=validation_engine,
                key_column=key_column,
            )
            self._merge_stats(stats, batch_stats)

        self.flush()
        return stats

    def publish_csv(
        self,
        csv_path: str | Path,
        validation_engine: ValidationEngine,
        key_column: str | None = None,
    ) -> dict[str, int]:
        """Read a CSV source in chunks, validate records, and publish valid rows."""
        source_path = Path(csv_path)
        stats = self._empty_stats()
        self.connect()

        logger.info(
            "CSV publishing started",
            extra={
                "pipeline_stage": "ingestion",
                "extra_fields": {"topic": self.topic, "csv_path": str(source_path)},
            },
        )

        try:
            for batch in pd.read_csv(source_path, chunksize=self.batch_size):
                if self.shutdown_event.is_set():
                    logger.warning(
                        "CSV publishing interrupted by shutdown request",
                        extra={
                            "pipeline_stage": "ingestion",
                            "extra_fields": {"topic": self.topic},
                        },
                    )
                    break

                batch_stats = self._publish_batch(
                    batch=batch,
                    validation_engine=validation_engine,
                    key_column=key_column,
                )
                self._merge_stats(stats, batch_stats)

            self.flush()
            self.monitoring.record_success(
                self.component_name,
                execution_id="publish_csv",
                duration_ms=0.0,
            )
            logger.info(
                "CSV publishing completed",
                extra={
                    "pipeline_stage": "ingestion",
                    "extra_fields": {"topic": self.topic, "stats": stats},
                },
            )
            return stats
        except Exception as exc:
            self.monitoring.record_failure(
                self.component_name,
                execution_id="publish_csv",
                duration_ms=0.0,
                error=exc,
            )
            logger.exception(
                "CSV publishing failed",
                extra={
                    "pipeline_stage": "ingestion",
                    "extra_fields": {"topic": self.topic, "csv_path": str(source_path)},
                },
            )
            raise

    def flush(self) -> None:
        """Flush pending Kafka messages."""
        if self.producer is not None:
            self.producer.flush(timeout=self.request_timeout_ms / 1_000)

    def __enter__(self) -> "BaseProducer":
        """Return a connected context-managed producer."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Close the producer on context manager exit."""
        self.close()

    def _publish_batch(
        self,
        batch: pd.DataFrame,
        validation_engine: ValidationEngine,
        key_column: str | None,
    ) -> dict[str, int]:
        """Validate a batch and publish records that pass validation."""
        stats = self._empty_stats()
        report = validation_engine.run(batch)
        invalid_indices = self._invalid_indices(report)

        for row_index, row in batch.iterrows():
            if self.shutdown_event.is_set():
                break

            stats["processed"] += 1
            record = self._normalize_record(row.to_dict())

            if row_index in invalid_indices:
                stats["skipped_invalid"] += 1
                logger.warning(
                    "Invalid record skipped",
                    extra={
                        "pipeline_stage": "validation",
                        "extra_fields": {
                            "topic": self.topic,
                            "row_index": int(row_index),
                        },
                    },
                )
                continue

            key = self._record_key(record=record, key_column=key_column)
            if self._send_with_retry(record=record, key=key):
                stats["published"] += 1
            else:
                stats["failed"] += 1

        self.flush()
        return stats

    def _send_with_retry(self, record: dict[str, Any], key: str | None) -> bool:
        """Send one record to Kafka and retry transient producer failures."""
        if self.producer is None:
            raise RuntimeError("Kafka producer is not connected.")

        for attempt in range(1, self.retry_count + 1):
            try:
                future = self.producer.send(self.topic, key=key, value=record)
                future.add_callback(self._on_delivery_success, key)
                future.add_errback(self._on_delivery_error, key)
                future.get(timeout=self.request_timeout_ms / 1_000)
                return True
            except KafkaError as exc:
                self._log_send_retry(attempt=attempt, error=exc)
            except Exception as exc:
                self._log_send_retry(attempt=attempt, error=exc)

            if attempt < self.retry_count:
                time.sleep(self.retry_backoff_seconds * attempt)

        return False

    def _on_delivery_success(self, metadata: Any, key: str | None) -> None:
        """Handle successful Kafka delivery callback events."""
        report = DeliveryReport(
            topic=metadata.topic,
            partition=metadata.partition,
            offset=metadata.offset,
            key=key,
        )
        logger.debug(
            "Kafka message delivered",
            extra={
                "pipeline_stage": "ingestion",
                "extra_fields": {
                    "topic": report.topic,
                    "partition": report.partition,
                    "offset": report.offset,
                    "key": report.key,
                },
            },
        )
        if self.delivery_callback is not None:
            self.delivery_callback(report)

    def _on_delivery_error(self, error: BaseException, key: str | None) -> None:
        """Handle failed Kafka delivery callback events."""
        report = DeliveryReport(
            topic=self.topic,
            partition=None,
            offset=None,
            key=key,
            error=str(error),
        )
        logger.error(
            "Kafka message delivery failed",
            extra={
                "pipeline_stage": "ingestion",
                "extra_fields": {"topic": self.topic, "key": key, "error": str(error)},
            },
        )
        if self.delivery_callback is not None:
            self.delivery_callback(report)

    def _log_send_retry(self, attempt: int, error: BaseException) -> None:
        """Log retry attempts and final send failures."""
        log_method = logger.warning if attempt < self.retry_count else logger.error
        log_method(
            "Kafka send attempt failed",
            extra={
                "pipeline_stage": "ingestion",
                "extra_fields": {
                    "topic": self.topic,
                    "attempt": attempt,
                    "retry_count": self.retry_count,
                    "error": str(error),
                },
            },
        )

    def _producer_config(self) -> dict[str, Any]:
        """Build KafkaProducer settings for local Kafka or Confluent Cloud."""
        config: dict[str, Any] = {
            "bootstrap_servers": self._bootstrap_servers(),
            "value_serializer": lambda v: json.dumps(v).encode("utf-8"),
            "key_serializer": lambda k: k.encode("utf-8") if k else None,
            "acks": "all",
            "retries": self.retry_count,
            "retry_backoff_ms": int(self.retry_backoff_seconds * 1_000),
            "request_timeout_ms": self.request_timeout_ms,
            "linger_ms": self.linger_ms,
        }

        if self.settings.kafka_api_key and self.settings.kafka_api_secret:
            config.update(
                {
                    "security_protocol": self.settings.kafka_security_protocol,
                    "sasl_mechanism": self.settings.kafka_sasl_mechanism,
                    "sasl_plain_username": self.settings.kafka_api_key,
                    "sasl_plain_password": self.settings.kafka_api_secret,
                }
            )

        return config

    def _bootstrap_servers(self) -> str:
        """Return Confluent Cloud bootstrap servers or local Kafka fallback."""
        if self.settings.kafka_api_key:
            if not self.settings.kafka_api_secret:
                raise ValueError("KAFKA_API_SECRET is required when KAFKA_API_KEY is set.")

            if self.settings.kafka_bootstrap_server == LOCAL_KAFKA_BOOTSTRAP_SERVER:
                return CONFLUENT_CLOUD_BOOTSTRAP_SERVER

            return self.settings.kafka_bootstrap_server

        return LOCAL_KAFKA_BOOTSTRAP_SERVER

    @staticmethod
    def _serialize_value(value: dict[str, Any]) -> bytes:
        """Serialize Kafka message values as JSON bytes."""
        return json.dumps(value, default=str, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _serialize_key(key: str | None) -> bytes | None:
        """Serialize Kafka message keys as UTF-8 bytes."""
        return key.encode("utf-8") if key is not None else None

    @staticmethod
    def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
        """Convert pandas null values to JSON null-compatible values."""
        return {key: None if pd.isna(value) else value for key, value in record.items()}

    @staticmethod
    def _invalid_indices(report: QualityReport) -> set[Any]:
        """Collect row indices failed by the validation framework."""
        invalid_indices: set[Any] = set()
        for result in report.failed_checks:
            if result.failed_indices:
                invalid_indices.update(result.failed_indices)
        return invalid_indices

    @staticmethod
    def _record_key(record: dict[str, Any], key_column: str | None) -> str | None:
        """Return the Kafka message key from the configured record column."""
        if key_column is None:
            return None

        value = record.get(key_column)
        return None if value is None else str(value)

    @staticmethod
    def _empty_stats() -> dict[str, int]:
        """Return the standard producer statistics payload."""
        return {
            "processed": 0,
            "published": 0,
            "skipped_invalid": 0,
            "failed": 0,
        }

    @staticmethod
    def _merge_stats(target: dict[str, int], source: dict[str, int]) -> None:
        """Merge source statistics into target statistics."""
        for key, value in source.items():
            target[key] += value

    def _register_shutdown_handlers(self) -> None:
        """Register signal handlers for graceful producer shutdown."""
        try:
            signal.signal(signal.SIGINT, self._request_shutdown)
            signal.signal(signal.SIGTERM, self._request_shutdown)
        except ValueError:
            logger.debug("Signal handlers can only be registered on the main thread.")

    def _request_shutdown(self, signum: int, frame: FrameType | None) -> None:
        """Request a graceful shutdown from an operating system signal."""
        self.shutdown_event.set()
        logger.warning(
            "Graceful shutdown requested",
            extra={
                "pipeline_stage": "ingestion",
                "extra_fields": {"topic": self.topic, "signal": signum},
            },
        )

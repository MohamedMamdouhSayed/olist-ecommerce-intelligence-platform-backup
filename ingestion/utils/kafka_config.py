"""Kafka configuration value object for future producer and consumer modules."""

from dataclasses import dataclass

from configs import settings


class KafkaConfig:
    """Configuration values required by future Kafka clients."""

    def __init__(self, topic: str | None = None):
        self.bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVER
        self.default_topic: str = topic or settings.KAFKA_TOPIC_ORDERS
        self.client_id: str = f"{settings.PROJECT_NAME}-ingestion-client"
        self.acks: str = "all"
        self.retries: int = 3
        self.batch_size: int = 16384


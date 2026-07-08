"""Shared Bronze Structured Streaming framework for Confluent Kafka sources."""

from __future__ import annotations

from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.types import StructType


DEFAULT_PROCESSING_TIME = "10 seconds"
DEFAULT_STARTING_OFFSETS = "earliest"
DEFAULT_FAIL_ON_DATA_LOSS = "false"


def stream_to_bronze(
    topic: str,
    schema: StructType,
    output_path: str,
    checkpoint_path: str,
    bootstrap_servers: str,
    api_key: str,
    api_secret: str,
    processing_time: str = DEFAULT_PROCESSING_TIME,
    spark_session: SparkSession | None = None,
) -> StreamingQuery:
    """Stream JSON Kafka records from Confluent Cloud into a Bronze Delta path."""
    spark_instance = spark_session or _active_spark_session()
    _validate_stream_config(
        topic=topic,
        schema=schema,
        output_path=output_path,
        checkpoint_path=checkpoint_path,
        bootstrap_servers=bootstrap_servers,
        api_key=api_key,
        api_secret=api_secret,
    )

    query: StreamingQuery | None = None

    try:
        kafka_stream = _read_kafka_stream(
            spark=spark_instance,
            topic=topic,
            bootstrap_servers=bootstrap_servers,
            api_key=api_key,
            api_secret=api_secret,
        )
        bronze_stream = _parse_bronze_payload(kafka_stream, schema)
        query = _write_delta_stream(
            dataframe=bronze_stream,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            processing_time=processing_time,
        )
        _monitor_query(query)
        return query
    except KeyboardInterrupt:
        if query is not None and query.isActive:
            query.stop()
        raise
    except Exception as exc:
        if query is not None and query.isActive:
            query.stop()
        raise RuntimeError(f"Bronze streaming failed for topic '{topic}'.") from exc


def build_jaas_config(api_key: str, api_secret: str) -> str:
    """Build the Kafka SASL JAAS config for Confluent Cloud."""
    return (
        "org.apache.kafka.common.security.plain.PlainLoginModule required "
        f'username="{_escape_jaas_value(api_key)}" '
        f'password="{_escape_jaas_value(api_secret)}";'
    )


def print_query_metrics(query: StreamingQuery) -> None:
    """Print streaming query status and throughput metrics."""
    progress = query.lastProgress or {}
    input_rows_per_second = progress.get("inputRowsPerSecond", 0.0)
    processed_rows_per_second = progress.get("processedRowsPerSecond", 0.0)

    print(f"Streaming query id: {query.id}")
    print(f"Streaming query name: {query.name}")
    print(f"Streaming query active: {query.isActive}")
    print(f"Streaming query status: {query.status}")
    print(f"inputRowsPerSecond: {input_rows_per_second}")
    print(f"processedRowsPerSecond: {processed_rows_per_second}")


def _read_kafka_stream(
    spark: SparkSession,
    topic: str,
    bootstrap_servers: str,
    api_key: str,
    api_secret: str,
) -> DataFrame:
    """Read Kafka key/value records and expose standard Kafka metadata."""
    return (
        spark.readStream.format("kafka")
        .options(
            **{
                "kafka.bootstrap.servers": bootstrap_servers,
                "subscribe": topic,
                "kafka.security.protocol": "SASL_SSL",
                "kafka.sasl.mechanism": "PLAIN",
                "kafka.sasl.jaas.config": build_jaas_config(api_key, api_secret),
                "startingOffsets": DEFAULT_STARTING_OFFSETS,
                "failOnDataLoss": DEFAULT_FAIL_ON_DATA_LOSS,
            }
        )
        .load()
        .select(
            col("key").cast("string").alias("kafka_key"),
            col("value").cast("string").alias("kafka_value"),
            col("topic").alias("kafka_topic"),
            col("partition").alias("kafka_partition"),
            col("offset").alias("kafka_offset"),
            col("timestamp").alias("kafka_timestamp"),
        )
    )


def _parse_bronze_payload(kafka_stream: DataFrame, schema: StructType) -> DataFrame:
    """Parse Kafka JSON values and add Bronze ingestion metadata columns."""
    parsed_payload = from_json(col("kafka_value"), schema)
    payload_columns = [field.name for field in schema.fields]

    return (
        kafka_stream.withColumn("payload", parsed_payload)
        .select(
            "kafka_key",
            "kafka_topic",
            "kafka_partition",
            "kafka_offset",
            "kafka_timestamp",
            current_timestamp().alias("bronze_ingested_at"),
            *[col(f"payload.{column_name}").alias(column_name) for column_name in payload_columns],
        )
    )


def _write_delta_stream(
    dataframe: DataFrame,
    output_path: str,
    checkpoint_path: str,
    processing_time: str,
) -> StreamingQuery:
    """Write a Bronze stream to Delta Lake using append mode and checkpointing."""
    return (
        dataframe.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .trigger(processingTime=processing_time)
        .start(output_path)
    )


def _monitor_query(query: StreamingQuery) -> None:
    """Print query metrics until the streaming query terminates."""
    print_query_metrics(query)

    while query.isActive:
        terminated = query.awaitTermination(timeout=10)
        print_query_metrics(query)

        if terminated:
            break


def _validate_stream_config(
    topic: str,
    schema: StructType,
    output_path: str,
    checkpoint_path: str,
    bootstrap_servers: str,
    api_key: str,
    api_secret: str,
) -> None:
    """Validate required Bronze streaming configuration."""
    required_values: dict[str, Any] = {
        "topic": topic,
        "schema": schema,
        "output_path": output_path,
        "checkpoint_path": checkpoint_path,
        "bootstrap_servers": bootstrap_servers,
        "api_key": api_key,
        "api_secret": api_secret,
    }
    missing_values = [name for name, value in required_values.items() if not value]

    if missing_values:
        raise ValueError(
            "Missing required Bronze streaming configuration values: "
            + ", ".join(missing_values)
        )

    if not schema.fields:
        raise ValueError("Bronze streaming schema must contain at least one field.")


def _active_spark_session() -> SparkSession:
    """Return the active Databricks Spark session."""
    active_session = SparkSession.getActiveSession()
    if active_session is None:
        raise RuntimeError("No active SparkSession is available.")

    return active_session


def _escape_jaas_value(value: str) -> str:
    """Escape values embedded in Kafka SASL JAAS config strings."""
    return value.replace("\\", "\\\\").replace('"', '\\"')

# Databricks notebook source
"""Stream Olist orders from Confluent Cloud Kafka into Bronze Delta Lake.

This notebook is compatible with Databricks Runtime 14+ and uses Spark
Structured Streaming to continuously ingest JSON order events from Kafka.
"""

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, current_timestamp, from_json
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.types import StringType, StructField, StructType

# COMMAND ----------

# Configure these values before running the notebook.
# For production jobs, prefer Databricks secrets:
# API_KEY = dbutils.secrets.get(scope="olist-confluent", key="api-key")
# API_SECRET = dbutils.secrets.get(scope="olist-confluent", key="api-secret")
BOOTSTRAP_SERVERS = "pkc-921jm.us-east-2.aws.confluent.cloud:9092"
TOPIC = "orders"
API_KEY = ""
API_SECRET = ""

OUTPUT_PATH = "dbfs:/mnt/olist/bronze/orders"
CHECKPOINT_PATH = "dbfs:/mnt/olist/checkpoints/orders"
PROCESSING_TIME = "10 seconds"

# COMMAND ----------

ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

orders_schema = StructType(
    [StructField(column_name, StringType(), nullable=True) for column_name in ORDER_COLUMNS]
)

# COMMAND ----------

def escape_jaas_value(value: str) -> str:
    """Escape values embedded in the Kafka SASL JAAS config string."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_jaas_config(api_key: str, api_secret: str) -> str:
    """Build the Confluent Cloud SASL JAAS configuration."""
    return (
        "org.apache.kafka.common.security.plain.PlainLoginModule required "
        f'username="{escape_jaas_value(api_key)}" '
        f'password="{escape_jaas_value(api_secret)}";'
    )


def validate_configuration() -> None:
    """Validate required streaming configuration before starting the query."""
    required_values = {
        "BOOTSTRAP_SERVERS": BOOTSTRAP_SERVERS,
        "TOPIC": TOPIC,
        "API_KEY": API_KEY,
        "API_SECRET": API_SECRET,
        "OUTPUT_PATH": OUTPUT_PATH,
        "CHECKPOINT_PATH": CHECKPOINT_PATH,
    }
    missing_values = [name for name, value in required_values.items() if not value]

    if missing_values:
        raise ValueError(
            "Missing required notebook configuration values: "
            + ", ".join(missing_values)
        )


def kafka_options() -> dict[str, str]:
    """Return Kafka read options for Confluent Cloud."""
    return {
        "kafka.bootstrap.servers": BOOTSTRAP_SERVERS,
        "subscribe": TOPIC,
        "kafka.security.protocol": "SASL_SSL",
        "kafka.sasl.mechanism": "PLAIN",
        "kafka.sasl.jaas.config": build_jaas_config(API_KEY, API_SECRET),
        "startingOffsets": "earliest",
        "failOnDataLoss": "false",
    }


def read_orders_from_kafka() -> DataFrame:
    """Read raw Kafka key/value records and cast both fields to string."""
    return (
        spark.readStream.format("kafka")
        .options(**kafka_options())
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


def parse_order_payload(raw_orders: DataFrame) -> DataFrame:
    """Parse JSON order payloads into the inferred Olist orders schema."""
    parsed_payload = from_json(col("kafka_value"), orders_schema)

    return (
        raw_orders.withColumn("payload", parsed_payload)
        .select(
            "kafka_key",
            "kafka_value",
            "kafka_topic",
            "kafka_partition",
            "kafka_offset",
            "kafka_timestamp",
            current_timestamp().alias("bronze_ingested_at"),
            *[col(f"payload.{column_name}").alias(column_name) for column_name in ORDER_COLUMNS],
        )
    )


def start_delta_stream(orders: DataFrame) -> StreamingQuery:
    """Start the Bronze Delta append stream with checkpointing."""
    return (
        orders.writeStream.format("delta")
        .outputMode("append")
        .option("checkpointLocation", CHECKPOINT_PATH)
        .trigger(processingTime=PROCESSING_TIME)
        .start(OUTPUT_PATH)
    )


def print_query_metrics(query: StreamingQuery) -> None:
    """Print query status and key throughput metrics."""
    progress = query.lastProgress or {}
    input_rows_per_second = progress.get("inputRowsPerSecond", 0.0)
    processed_rows_per_second = progress.get("processedRowsPerSecond", 0.0)

    print(f"Streaming query id: {query.id}")
    print(f"Streaming query name: {query.name}")
    print(f"Streaming query active: {query.isActive}")
    print(f"Streaming query status: {query.status}")
    print(f"inputRowsPerSecond: {input_rows_per_second}")
    print(f"processedRowsPerSecond: {processed_rows_per_second}")


def monitor_query(query: StreamingQuery) -> None:
    """Continuously print streaming query status while the stream is active."""
    print_query_metrics(query)

    while query.isActive:
        terminated = query.awaitTermination(timeout=10)
        print_query_metrics(query)

        if terminated:
            break

# COMMAND ----------

query = None

try:
    validate_configuration()

    raw_orders_stream = read_orders_from_kafka()
    bronze_orders_stream = parse_order_payload(raw_orders_stream)
    query = start_delta_stream(bronze_orders_stream)

    monitor_query(query)
except KeyboardInterrupt:
    print("Streaming query interrupted by user.")
    if query is not None:
        query.stop()
        print_query_metrics(query)
except Exception as exc:
    print(f"Streaming query failed: {exc}")
    if query is not None:
        print_query_metrics(query)
        query.stop()
    raise

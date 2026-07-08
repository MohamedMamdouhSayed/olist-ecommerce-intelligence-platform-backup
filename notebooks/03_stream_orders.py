# Databricks notebook source
"""Stream Olist orders from Confluent Cloud Kafka into Bronze Delta Lake."""

# COMMAND ----------

from streaming.framework import stream_to_bronze
from streaming.schemas import OrdersSchema

# COMMAND ----------

# Dataset configuration. For production, populate API_KEY and API_SECRET from
# Databricks secrets instead of literal values.
TABLE_NAME = "orders"
TOPIC = "orders"
SCHEMA = OrdersSchema
OUTPUT_PATH = "dbfs:/mnt/olist/bronze/orders"
CHECKPOINT_PATH = "dbfs:/mnt/olist/checkpoints/orders"

BOOTSTRAP_SERVERS = "pkc-921jm.us-east-2.aws.confluent.cloud:9092"
API_KEY = ""
API_SECRET = ""

# COMMAND ----------

query = stream_to_bronze(
    topic=TOPIC,
    schema=SCHEMA,
    output_path=OUTPUT_PATH,
    checkpoint_path=CHECKPOINT_PATH,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    api_key=API_KEY,
    api_secret=API_SECRET,
)

"""Reusable Spark schemas for Olist Bronze streaming ingestion."""

from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType


def _string_schema(column_names: list[str]) -> StructType:
    """Build a nullable string schema for raw Bronze ingestion."""
    return StructType(
        [StructField(column_name, StringType(), nullable=True) for column_name in column_names]
    )


OrdersSchema = _string_schema(
    [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
)

CustomersSchema = _string_schema(
    [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ]
)

ProductsSchema = StructType(
    [
        StructField("product_id", StringType(), nullable=True),
        StructField("product_category_name", StringType(), nullable=True),
        StructField("product_name_lenght", IntegerType(), nullable=True),
        StructField("product_description_lenght", IntegerType(), nullable=True),
        StructField("product_photos_qty", IntegerType(), nullable=True),
        StructField("product_weight_g", IntegerType(), nullable=True),
        StructField("product_length_cm", IntegerType(), nullable=True),
        StructField("product_height_cm", IntegerType(), nullable=True),
        StructField("product_width_cm", IntegerType(), nullable=True),
    ]
)

SellersSchema = _string_schema(
    [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ]
)

OrderItemsSchema = StructType(
    [
        StructField("order_id", StringType(), nullable=True),
        StructField("order_item_id", IntegerType(), nullable=True),
        StructField("product_id", StringType(), nullable=True),
        StructField("seller_id", StringType(), nullable=True),
        StructField("shipping_limit_date", StringType(), nullable=True),
        StructField("price", DoubleType(), nullable=True),
        StructField("freight_value", DoubleType(), nullable=True),
    ]
)

PaymentsSchema = StructType(
    [
        StructField("order_id", StringType(), nullable=True),
        StructField("payment_sequential", IntegerType(), nullable=True),
        StructField("payment_type", StringType(), nullable=True),
        StructField("payment_installments", IntegerType(), nullable=True),
        StructField("payment_value", DoubleType(), nullable=True),
    ]
)

ReviewsSchema = _string_schema(
    [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ]
)

GeolocationSchema = StructType(
    [
        StructField("geolocation_zip_code_prefix", StringType(), nullable=True),
        StructField("geolocation_lat", DoubleType(), nullable=True),
        StructField("geolocation_lng", DoubleType(), nullable=True),
        StructField("geolocation_city", StringType(), nullable=True),
        StructField("geolocation_state", StringType(), nullable=True),
    ]
)

CategoryTranslationSchema = _string_schema(
    [
        "product_category_name",
        "product_category_name_english",
    ]
)

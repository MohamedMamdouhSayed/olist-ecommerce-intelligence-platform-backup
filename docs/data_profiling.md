# 📊 Data Profiling & Inventory Report
## Olist E-Commerce Intelligence Platform

---

| Field | Detail |
|---|---|
| **Project Name** | Olist E-Commerce Intelligence Platform |
| **Dataset Name** | Brazilian E-Commerce Public Dataset by Olist |
| **Document Version** | v1.0.0 |
| **Last Updated** | July 2025 |
| **Authors** | Mohamed Mamdouh · Christen Nashat · Tasbeeh Ahmed · Martina Farah · Mai Ahmed · Alaa Ramadan |
| **Status** | ✅ Active |

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Dataset Overview](#dataset-overview)
3. [Data Architecture Context](#data-architecture-context)
4. [Data Inventory](#data-inventory)
5. [Detailed Table Documentation](#detailed-table-documentation)
   - [customers](#-table-customers)
   - [orders](#-table-orders)
   - [order_items](#-table-order_items)
   - [order_payments](#-table-order_payments)
   - [order_reviews](#-table-order_reviews)
   - [products](#-table-products)
   - [sellers](#-table-sellers)
   - [geolocation](#-table-geolocation)
   - [product_category_translation](#-table-product_category_translation)
6. [Entity Relationship Summary](#entity-relationship-summary)
7. [Medallion Architecture Mapping](#medallion-architecture-mapping)
8. [Data Engineering Considerations](#data-engineering-considerations)
9. [Key Insights from Profiling](#key-insights-from-profiling)

---

## Executive Summary

The **Olist Brazilian E-Commerce Dataset** is a real-world, anonymised transactional dataset released publicly by Olist — Brazil's largest online marketplace aggregator. It captures the full customer purchasing journey across approximately **100,000 orders** placed between **2016 and 2018**, spanning orders, payments, logistics, product catalogue, seller information, and customer reviews.

### Why This Dataset Matters

This dataset is analytically rich precisely because it is messy in realistic ways: it contains null delivery timestamps, referential edge cases, geolocation duplicates, and Portuguese-language free-text reviews. These characteristics make it an ideal foundation for demonstrating production-grade data engineering practices.

> **📌 Note:** The dataset reflects a real marketplace operating in Brazil. Insights derived from this data carry genuine business relevance — particularly around logistics performance, customer retention, and payment behaviour in an emerging market context.

### Architectural Role

Within the **Olist E-Commerce Intelligence Platform**, this dataset serves as the sole source of truth for all analytical, ML, and reporting workloads. It enters the system as raw CSV files and is progressively refined through a **Medallion Architecture** (Bronze → Silver → Gold) before landing in a **Microsoft Fabric Warehouse** to power **Power BI** dashboards and **Machine Learning** models deployed via **FastAPI** and **Streamlit**.

---

## Dataset Overview

| Attribute | Value |
|---|---|
| **Source** | [Kaggle — Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) |
| **Number of Tables** | 9 |
| **Total Raw Records** | ~1,551,021 rows (across all tables) |
| **Date Range** | September 2016 – October 2018 |
| **Business Domain** | E-Commerce · Retail · Logistics · Customer Experience |
| **Granularity** | Order-item level (finest); order level (primary analytical unit) |
| **Language** | Portuguese (review text); English (column names and category translations) |
| **License** | CC BY-NC-SA 4.0 |
| **Storage Format (Raw)** | CSV (UTF-8 encoded) |

---

## Data Architecture Context

The dataset flows through the platform in a structured, layered pipeline. Each layer has a distinct contract, storage format, and quality guarantee.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OLIST DATA PIPELINE                                 │
│                                                                             │
│  CSV Files          Bronze              Silver              Gold            │
│  (Raw Source)  ──►  (ADLS Gen2)  ──►  (Databricks)  ──►  (Fabric DWH)     │
│                     Delta / Parquet    PySpark + dbt       Star Schema      │
│                     Append-only        Cleansed             Aggregated       │
│                     No transforms      Validated            Business-ready   │
│                                                                             │
│                                             ▼                  ▼           │
│                                          Power BI          FastAPI / ML    │
│                                        Dashboards         Streamlit App    │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Layer | Platform | Format | Responsibility |
|---|---|---|---|
| **Raw** | Local / ADLS Gen2 landing zone | CSV | Source files, immutable, no processing |
| **Bronze** | Azure Data Lake Storage Gen2 via Kafka | Delta Lake (Parquet) | Raw ingestion, append-only, schema-on-read |
| **Silver** | Databricks (PySpark) | Delta Lake | Cleansing, deduplication, type casting, null handling, joins |
| **Gold** | dbt + Microsoft Fabric Warehouse | Delta / SQL | Dimensional models, KPI aggregations, ML feature tables |
| **Serving** | Power BI · FastAPI · Streamlit | DirectQuery / API | Business dashboards and ML inference endpoints |

> **⚠️ Warning:** Raw CSV files must be treated as immutable. Any transformation should occur in Bronze or later layers. Never write back to the source files.

---

## Data Inventory

| Table | Description | Rows | Columns | Grain | Primary Key | Foreign Keys |
|---|---|---|---|---|---|---|
| `customers` | Customer identity and location | 99,441 | 5 | One row per customer | `customer_id` | → `orders.customer_id` |
| `orders` | Order lifecycle and status | 99,441 | 8 | One row per order | `order_id` | `customer_id` → `customers` |
| `order_items` | Individual items within each order | 112,650 | 7 | One row per item per order | `(order_id, order_item_id)` | `order_id` → `orders`, `product_id` → `products`, `seller_id` → `sellers` |
| `order_payments` | Payment transactions per order | 103,886 | 5 | One row per payment method per order | `(order_id, payment_sequential)` | `order_id` → `orders` |
| `order_reviews` | Customer satisfaction surveys | 99,224 | 7 | One row per review | `review_id` | `order_id` → `orders` |
| `products` | Product catalogue with attributes | 32,951 | 9 | One row per product SKU | `product_id` | → `order_items.product_id`, `product_category_name` → `translation` |
| `sellers` | Seller profiles and locations | 3,095 | 4 | One row per seller | `seller_id` | → `order_items.seller_id` |
| `geolocation` | Brazilian ZIP code coordinates | 1,000,163 (261,831 dupes) | 5 | One row per ZIP + lat/lng pair | `(geolocation_zip_code_prefix, lat, lng)` | `zip_code` → `customers`, `sellers` |
| `product_category_translation` | Portuguese → English category names | 71 | 2 | One row per category | `product_category_name` | → `products.product_category_name` |

> **📌 Note:** The `geolocation` table contains **261,831 duplicate ZIP code entries** due to Brazilian ZIP codes (CEPs) covering multiple streets with different coordinates. Deduplication to first occurrence per ZIP is applied in the Silver layer.

---

## Detailed Table Documentation

---

### 👤 Table: `customers`

#### Purpose
Stores the unique identity and geographic location of each customer. Because Olist uses a pseudonymisation strategy, `customer_id` is unique per order — a single physical customer who places two orders will appear as two records. `customer_unique_id` is the true de-duplicated customer identifier.

#### Business Questions Supported
- How many unique customers does Olist have?
- What is the geographic distribution of customers across Brazilian states?
- Which cities generate the highest order volumes?
- What is the true repeat purchase rate (requires `customer_unique_id`)?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 99,441 |
| **Columns** | 5 |
| **Unique Customers (`customer_unique_id`)** | 96,096 |
| **Duplicate Customer IDs** | 0 (each `customer_id` is unique per order) |
| **Null Values** | 0 across all columns |
| **States Represented** | 27 |
| **Cities Represented** | 4,119 |

#### Granularity
One row represents one customer **per order context**. A physical customer who placed 3 orders will have 3 `customer_id` values, all sharing the same `customer_unique_id`.

#### Primary Key
`customer_id`

#### Foreign Keys
Referenced by: `orders.customer_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `customer_id` | `STRING` | Order-scoped customer ID (pseudonymised) | `06b8999e2fba1a1fbc88172c00ba8bc7` | No |
| `customer_unique_id` | `STRING` | True customer identifier across orders | `861eff4711a542e4b93843c6dd7febb0` | No |
| `customer_zip_code_prefix` | `STRING` | First 5 digits of Brazilian ZIP (CEP) | `14409` | No |
| `customer_city` | `STRING` | Customer city name (lower-case) | `franca` | No |
| `customer_state` | `STRING` | 2-letter state code | `SP` | No |

#### Data Quality Notes

- **No nulls detected** in any column — this table is the cleanest in the dataset.
- `customer_city` values are in inconsistent casing (all lowercase, some with accents stripped). Standardise in Silver.
- The distinction between `customer_id` and `customer_unique_id` is a **critical business logic trap**. Joining on `customer_id` counts orders; joining on `customer_unique_id` counts customers. Always document which key is used in downstream models.
- **3,345 customers** have placed more than one order (3.0% repeat rate) — a significant business concern documented in the EDA.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Ingested as-is from CSV. Schema enforced via Delta. |
| **Silver** | City name standardised (title case, accent normalisation). ZIP joined to `geolocation` to enrich with lat/lng. |
| **Gold / dbt** | `dim_customers` dimension table in star schema. SCD Type 2 tracking not applicable (static snapshot dataset). |
| **Power BI** | Customer geographic distribution map. State/city drill-down filters. |
| **Machine Learning** | `customer_unique_id` used to aggregate RFM (Recency, Frequency, Monetary) features for churn prediction. |

---

### 📦 Table: `orders`

#### Purpose
The central fact-like entity of the Olist dataset. Records the full lifecycle of each order from creation through approval, shipment, and delivery. Contains five timestamp columns that enable delivery performance analysis.

#### Business Questions Supported
- What is the order approval time distribution?
- What percentage of orders are delivered on time?
- How many orders were cancelled, and at what stage?
- What is the average end-to-end fulfilment time?
- What is the overall order conversion rate?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 99,441 |
| **Columns** | 8 |
| **Unique Orders** | 99,441 |
| **Delivered Orders** | 96,478 (97.0%) |
| **Cancelled Orders** | 625 (0.6%) |
| **Nulls: `order_approved_at`** | 160 (0.16%) |
| **Nulls: `order_delivered_carrier_date`** | 1,783 (1.79%) |
| **Nulls: `order_delivered_customer_date`** | 2,965 (2.98%) |
| **Negative time anomalies** | 1,603 (waiting time), 67 (shipping time) |

#### Granularity
One row represents one order. An order may contain multiple items (see `order_items`) and multiple payments (see `order_payments`).

#### Primary Key
`order_id`

#### Foreign Keys
- `customer_id` → `customers.customer_id`
- Referenced by: `order_items.order_id`, `order_payments.order_id`, `order_reviews.order_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `order_id` | `STRING` | Unique order identifier | `e481f51cbdc54678b7cc49136f2d6af7` | No |
| `customer_id` | `STRING` | Order-scoped customer reference | `9ef432eb6251297304e76186b10a928d` | No |
| `order_status` | `STRING` | Current order status | `delivered` | No |
| `order_purchase_timestamp` | `TIMESTAMP` | When the customer placed the order | `2017-10-02 10:56:33` | No |
| `order_approved_at` | `TIMESTAMP` | When payment was confirmed | `2017-10-02 11:07:15` | Yes |
| `order_delivered_carrier_date` | `TIMESTAMP` | When seller handed order to carrier | `2017-10-04 19:55:00` | Yes |
| `order_delivered_customer_date` | `TIMESTAMP` | When customer received the order | `2017-10-10 21:25:13` | Yes |
| `order_estimated_delivery_date` | `TIMESTAMP` | Estimated delivery shown to customer | `2017-10-18 00:00:00` | No |

#### Data Quality Notes

> **⚠️ Warning — Null Delivery Dates:** The 160 null `order_approved_at` values break down as: Cancelled (141), Delivered (14 — data corruption), Created/Limbo (5). Apply business-logic null handling, not blanket imputation.

- **Data corruption cases:** 2 specific order IDs are marked `delivered` but have `NULL` in all delivery timestamp columns. These must be **removed**, not imputed — they represent either test orders or upstream data corruption.
- **Imputation rule for carrier dates:** Where `order_delivered_customer_date` is present but `order_delivered_carrier_date` is null, impute as `customer_date - 3 days` (based on observed median shipping lag). Document this assumption in dbt model comments.
- **Negative durations:** 1,603 records where `order_delivered_carrier_date < order_approved_at`. Caused by timezone inconsistencies or data entry errors. Set computed duration to 0, flag records for review.
- **Order status values:** `delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing`, `created`, `approved`.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Full CSV load. Timestamps stored as strings, cast in Silver. |
| **Silver** | Cast all timestamps. Apply null imputation rules. Compute derived columns: `approval_time_hrs`, `waiting_time_days`, `shipping_time_days`, `total_delivery_days`, `is_late` (boolean). Remove corrupt records. |
| **Gold / dbt** | Central to `fact_sales` and `fact_deliveries`. `is_late` flag drives delivery performance KPIs. |
| **Power BI** | Delivery performance dashboard. On-time rate trend. Order status funnel. |
| **Machine Learning** | `is_late`, `total_delivery_days`, `approval_time_hrs` → churn prediction features. `order_purchase_timestamp` → demand forecasting time index. |

---

### 🛒 Table: `order_items`

#### Purpose
Records the individual line items within each order — one row per product per order. This is the most granular transactional table and the foundation for revenue, product, and seller analytics.

#### Business Questions Supported
- What is the revenue per product category?
- Which sellers have the highest sales volume?
- What is the average freight cost relative to product price?
- How many items are typically in a single order?
- What is the price distribution by product category?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 112,650 |
| **Columns** | 7 |
| **Unique Orders** | 98,666 |
| **Unique Products** | 32,951 |
| **Unique Sellers** | 3,095 |
| **Single-item Orders** | 83,684 (88.1%) |
| **Multi-item Orders** | 11,200 (11.9%) |
| **Null Values** | 0 |
| **Avg Price** | R$ 120.65 (σ = 184.11) |
| **Avg Freight** | R$ 19.99 |

#### Granularity
One row represents one item within one order. If an order contains 3 items, it has 3 rows in this table — each identified by `(order_id, order_item_id)`.

#### Primary Key
`(order_id, order_item_id)` — composite key

#### Foreign Keys
- `order_id` → `orders.order_id`
- `product_id` → `products.product_id`
- `seller_id` → `sellers.seller_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `order_id` | `STRING` | Parent order reference | `00010242fe8c5a6d1ba2dd792cb16214` | No |
| `order_item_id` | `INTEGER` | Item sequence number within order | `1` | No |
| `product_id` | `STRING` | Product sold | `4244733e06e7ecb4970a6e2e53e26c4b` | No |
| `seller_id` | `STRING` | Seller fulfilling this item | `48436dade18ac8b2bce089ec2a041202` | No |
| `shipping_limit_date` | `TIMESTAMP` | Deadline for seller to hand to carrier | `2017-09-19 09:45:35` | No |
| `price` | `DECIMAL` | Item price in Brazilian Reals (R$) | `58.90` | No |
| `freight_value` | `DECIMAL` | Freight cost for this item | `13.29` | No |

#### Data Quality Notes

- **No nulls** — cleanest transactional table after customers.
- `price` ranges from R$ 0.85 to R$ 6,735. Values below R$ 1 may represent promotional or test items — flag in Silver.
- **Freight as % of price** averages ~16.5%, but rises sharply for low-value items. This is analytically important: for items under R$ 30, freight often exceeds product price.
- Multi-item orders (those with `order_item_id > 1`) have a statistically lower review score (4.01 vs 4.09 for single-item). Coordinate with `order_reviews` in Gold models.
- Revenue calculation: `total_revenue = SUM(price) + SUM(freight_value)` per order. Do not use `order_payments.payment_value` for this — payments may include voucher discounts.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw CSV load. All numeric columns as string, cast in Silver. |
| **Silver** | Cast price/freight to `DECIMAL(10,2)`. Derive `item_total = price + freight_value`. Validate `price > 0`. |
| **Gold / dbt** | Core of `fact_sales`. Joined to `dim_products`, `dim_sellers`. Aggregated to order-level for `fact_orders`. |
| **Power BI** | Revenue by category, seller performance, freight burden analysis. |
| **Machine Learning** | Product features: `avg_price`, `total_revenue_by_product`, `avg_freight_ratio` → demand forecasting. Seller features: `seller_avg_price`, `seller_item_count` → seller analytics. |

---

### 💳 Table: `order_payments`

#### Purpose
Records all payment transactions associated with each order. An order may have multiple payment rows if the customer used more than one payment method (e.g., credit card + voucher). This table is essential for revenue validation and payment behaviour analysis.

#### Business Questions Supported
- What is the most common payment method?
- What percentage of customers use instalment plans?
- What is the average payment value by payment type?
- How does payment method correlate with order value and customer satisfaction?
- What is the voucher redemption rate?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 103,886 |
| **Columns** | 5 |
| **Unique Orders** | 99,440 |
| **Orders with Multiple Payment Methods** | ~4,446 |
| **Null Values** | 0 |
| **Credit Card Share** | 76,795 transactions (73.9%) |
| **Boleto Share** | 19,784 (19.0%) |
| **Voucher Share** | 5,775 (5.6%) |
| **Debit Card Share** | 1,529 (1.5%) |
| **Avg Payment Value** | R$ 172.73 (σ = 267.78) |

#### Granularity
One row represents one payment method used within one order. A single order split across credit card and voucher will have 2 rows.

#### Primary Key
`(order_id, payment_sequential)` — composite key

#### Foreign Keys
- `order_id` → `orders.order_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `order_id` | `STRING` | Parent order reference | `b81ef226f3fe1789b1e8b2acac839d17` | No |
| `payment_sequential` | `INTEGER` | Payment method sequence (1 = primary) | `1` | No |
| `payment_type` | `STRING` | Method: `credit_card`, `boleto`, `voucher`, `debit_card` | `credit_card` | No |
| `payment_installments` | `INTEGER` | Number of monthly instalments (1 = upfront) | `3` | No |
| `payment_value` | `DECIMAL` | Amount charged in R$ | `99.33` | No |

#### Data Quality Notes

- **Aggregation trap:** Joining `order_payments` to `orders` without aggregating first creates row duplication. Always `GROUP BY order_id, SUM(payment_value)` before joining to order-level tables.
- **3 records** have `payment_type = 'not_defined'` — exclude from payment method analysis, retain for revenue totals.
- **Voucher mechanics:** When `payment_type = 'voucher'`, `payment_value` represents the discount amount, not the full order value. Account for this when computing net revenue.
- **Instalment distribution:** 50.1% of credit card orders use instalments. High-instalment orders (6–24x) correlate strongly with high AOV — a key feature for customer segmentation.

> **💡 Tip:** For revenue analysis, use `SUM(payment_value)` from this table at the order level. For product-level revenue, use `price + freight_value` from `order_items` — the two won't match exactly due to voucher discounts.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw load. All columns exact. |
| **Silver** | Deduplicate by `order_id` after aggregation. Create `total_payment_value` per order. Derive `has_voucher` boolean, `max_installments`, `payment_method_count`. |
| **Gold / dbt** | `dim_payment_method` dimension. `payment_value` as measure on `fact_sales`. Instalment data → customer segmentation model. |
| **Power BI** | Payment method mix chart. Instalment distribution. Voucher usage KPI. |
| **Machine Learning** | `payment_type`, `payment_installments`, `has_voucher` → churn prediction features. Payment behaviour as proxy for customer financial profile. |

---

### ⭐ Table: `order_reviews`

#### Purpose
Captures customer satisfaction feedback submitted after order delivery. Each review includes a 1–5 star score and optional free-text comments in Portuguese. This table is the primary source for NLP analysis and customer sentiment modelling.

#### Business Questions Supported
- What is the platform's average review score?
- What percentage of orders receive bad reviews (≤ 3 stars)?
- What topics appear most frequently in negative vs positive reviews?
- How long after delivery do customers submit reviews?
- Which product categories and delivery performance factors drive bad reviews?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 99,224 |
| **Columns** | 7 |
| **Unique Reviews** | 98,410 |
| **Average Review Score** | 4.08 / 5.0 |
| **5-star Reviews** | 59,600 (60.1%) |
| **4-star Reviews** | 19,232 (19.4%) |
| **3-star Reviews** | 8,656 (8.7%) |
| **2-star Reviews** | 3,168 (3.2%) |
| **1-star Reviews** | 8,568 (8.6%) |
| **Bad Reviews (≤ 3 stars)** | 20,392 (23.04%) |
| **Reviews with comment text** | ~41,000 (~41%) |
| **Nulls: `review_comment_title`** | ~58,000 (no title provided) |
| **Nulls: `review_comment_message`** | ~58,000 (no message provided) |
| **Avg time to review after delivery** | 10h 29m (median: 6h 15m) |

#### Granularity
One row represents one customer review for one order. In rare cases, a single order has more than one review — the most recent should be used for analysis.

#### Primary Key
`review_id`

#### Foreign Keys
- `order_id` → `orders.order_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `review_id` | `STRING` | Unique review identifier | `7bc2406110b926393aa56f80a40eba40` | No |
| `order_id` | `STRING` | Order being reviewed | `73fc7af87114b39712e6da79b0a377eb` | No |
| `review_score` | `INTEGER` | Star rating (1–5) | `4` | No |
| `review_comment_title` | `STRING` | Short review title (Portuguese) | `Muito bom!` | Yes |
| `review_comment_message` | `STRING` | Full review text (Portuguese) | `Produto chegou antes do prazo!` | Yes |
| `review_creation_date` | `TIMESTAMP` | When review was submitted | `2018-01-18 00:00:00` | No |
| `review_answer_timestamp` | `TIMESTAMP` | When Olist responded (if applicable) | `2018-01-18 21:46:59` | No |

#### Data Quality Notes

> **⚠️ Warning — NLP Language:** All free-text review content is in **Brazilian Portuguese**. Standard English NLP tools (NLTK, spaCy `en_core_web_sm`) will not work correctly. Use `spacy[pt_core_news_sm]` or multilingual models (mBERT, BERTimbau) for tokenisation and sentiment analysis.

- **58% of reviews have no text** — only a star score. NLP models must gracefully handle empty strings; do not drop these rows as the score itself is valuable.
- **Statistical finding:** Late delivery orders have a **4x higher probability** of receiving a 1-star review (chi-square p < 0.001). This is the strongest signal in the entire dataset.
- **67% of 1-star review texts** mention delivery-related keywords (`entrega`, `prazo`, `atraso`). Only 12% mention product defects.
- Duplicate reviews per order exist — deduplicate by keeping the latest `review_creation_date` per `order_id`.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw load. Free-text stored as-is. |
| **Silver** | Deduplicate. Classify `review_sentiment` as `positive` (≥ 4), `neutral` (3), `negative` (≤ 2). Strip nulls from text for NLP processing. Compute `hours_to_review` from delivery timestamp. |
| **Gold / dbt** | `fact_reviews` table. `dim_review_score` dimension. Aggregated sentiment scores join to `fact_sales`. |
| **Power BI** | Customer satisfaction KPI tile. Review score distribution chart. Sentiment trend over time. |
| **Machine Learning** | NLP sentiment classification (BERTimbau fine-tuned on Portuguese reviews). Topic modelling (LDA) on negative review text. `review_score` as churn signal — orders with ≤ 2 stars have significantly higher churn probability. |

---

### 📦 Table: `products`

#### Purpose
The product catalogue. Contains physical attributes and category classifications for every product SKU that appears in the order history. Enables product performance analysis and feature engineering for demand forecasting.

#### Business Questions Supported
- Which product categories drive the most revenue?
- Do product dimensions and weight correlate with freight costs?
- Which products have the highest average review scores?
- What is the price distribution by category?
- Which categories are declining vs growing over the study period?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 32,951 |
| **Columns** | 9 |
| **Unique Categories (Portuguese)** | 74 |
| **Unique Categories (after translation)** | 71 |
| **Nulls: `product_category_name`** | 610 (1.9%) |
| **Nulls: `product_name_length`** | 610 (1.9%) |
| **Nulls: `product_description_length`** | 610 (1.9%) |
| **Nulls: `product_photos_qty`** | 610 (1.9%) |
| **Nulls: Physical dimensions** | 2 records |

#### Granularity
One row represents one unique product SKU (stock-keeping unit). Products are not versioned — if a seller changes a product's price, no new row is created.

#### Primary Key
`product_id`

#### Foreign Keys
- `product_category_name` → `product_category_translation.product_category_name`
- Referenced by: `order_items.product_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `product_id` | `STRING` | Unique product identifier (anonymised) | `1e9e8ef04dbcff4541ed26657ea517e5` | No |
| `product_category_name` | `STRING` | Category in Portuguese | `cama_mesa_banho` | Yes |
| `product_name_length` | `INTEGER` | Character count of product name | `58` | Yes |
| `product_description_length` | `INTEGER` | Character count of product description | `1020` | Yes |
| `product_photos_qty` | `INTEGER` | Number of product listing photos | `4` | Yes |
| `product_weight_g` | `INTEGER` | Product weight in grams | `650` | Yes |
| `product_length_cm` | `INTEGER` | Package length in cm | `28` | Yes |
| `product_height_cm` | `INTEGER` | Package height in cm | `9` | Yes |
| `product_width_cm` | `INTEGER` | Package width in cm | `15` | Yes |

#### Data Quality Notes

- **610 products** (1.9%) have null category names — likely unlisted or deleted categories. Assign to `'unknown'` category in Silver rather than dropping, as these products may still appear in order history.
- Physical dimensions (weight, length, height, width) can be used to **validate freight costs** — higher weight/volume should correlate with higher `freight_value` in `order_items`. Anomalies where small products have high freight may indicate data entry errors.
- Product names and descriptions are anonymised hashes — `product_name_length` and `product_description_length` serve as proxies for listing quality.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw CSV. All dimension columns as integers (nullable). |
| **Silver** | Join with `product_category_translation` to add English category name. Impute null categories as `'unknown'`. Compute `product_volume_cm3 = length * height * width`. |
| **Gold / dbt** | `dim_products` dimension. Category hierarchy derived from translation table. |
| **Power BI** | Category performance matrix. Revenue by category. Product photo count vs review score correlation. |
| **Machine Learning** | Demand forecasting features: `category`, `avg_price`, `avg_review_score`, `product_weight_g`. Feature: `photo_count` as proxy for listing quality in conversion rate modelling. |

---

### 🏪 Table: `sellers`

#### Purpose
Profiles each seller on the Olist marketplace, including their geographic location. Enables seller performance analysis, logistics routing, and identification of top/bottom performing merchants.

#### Business Questions Supported
- Which sellers have the highest order volumes and revenue?
- Which sellers have the lowest average delivery times?
- Are seller locations correlated with delivery speed?
- Which sellers generate the most bad reviews?
- What is the geographic distribution of sellers vs customers?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 3,095 |
| **Columns** | 4 |
| **Null Values** | 0 |
| **States Represented** | 23 |
| **São Paulo-based Sellers** | ~70% |

#### Granularity
One row represents one unique seller on the platform.

#### Primary Key
`seller_id`

#### Foreign Keys
Referenced by: `order_items.seller_id`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `seller_id` | `STRING` | Unique seller identifier (anonymised) | `3442f8959a84dea7ee197c632cb2df15` | No |
| `seller_zip_code_prefix` | `STRING` | First 5 digits of seller ZIP (CEP) | `13023` | No |
| `seller_city` | `STRING` | Seller city name | `campinas` | No |
| `seller_state` | `STRING` | 2-letter state code | `SP` | No |

#### Data Quality Notes

- City names are inconsistently cased (lowercase, some with accented characters stripped). Standardise in Silver.
- Approximately **70% of sellers are in São Paulo state (SP)** — creating a geographic concentration risk for delivery times to northern and northeastern Brazil.
- No seller performance metadata is stored in this table — all KPIs (revenue, avg review score, avg delivery time) must be computed by joining to `order_items` and `orders`.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw CSV. |
| **Silver** | City name standardisation. ZIP → lat/lng enrichment from `geolocation`. Derive seller state region (North, Northeast, Southeast, South, Centre-West). |
| **Gold / dbt** | `dim_sellers` dimension. Computed KPIs: `seller_total_orders`, `seller_avg_review_score`, `seller_avg_delivery_days`. |
| **Power BI** | Seller performance leaderboard. Seller geographic map. |
| **Machine Learning** | Seller features: `seller_avg_delivery_days`, `seller_bad_review_rate` → delivery delay prediction model. |

---

### 📍 Table: `geolocation`

#### Purpose
Maps Brazilian ZIP code prefixes (first 5 digits of the 8-digit CEP) to geographic coordinates (latitude, longitude) and named locations. Used to enrich customer and seller location data for geographic analysis and mapping.

#### Business Questions Supported
- Where are Olist customers concentrated geographically?
- Which states/cities have the highest order volumes?
- How does distance between customer and seller correlate with delivery time?
- What is the geographic coverage of Olist's seller network?

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Raw Rows** | 1,000,163 |
| **Duplicate Rows** | 261,831 (26.2%) |
| **Rows after deduplication** | 738,332 |
| **Unique ZIP Prefixes** | ~19,015 |
| **Null Values** | 0 |

#### Granularity
One row represents one latitude/longitude coordinate point for one ZIP code prefix. Because Brazilian CEPs cover entire streets (not buildings), a single ZIP prefix can have many valid coordinate pairs.

> **⚠️ Warning:** Do **not** use this table as-is. The 261,831 duplicate rows will cause fan-out joins (row multiplication) when joining to customers or sellers. Always deduplicate to first occurrence per `geolocation_zip_code_prefix` in the Silver layer before any join.

#### Primary Key
None in raw form. After deduplication: `geolocation_zip_code_prefix`

#### Foreign Keys
- `geolocation_zip_code_prefix` ↔ `customers.customer_zip_code_prefix`
- `geolocation_zip_code_prefix` ↔ `sellers.seller_zip_code_prefix`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `geolocation_zip_code_prefix` | `STRING` | First 5 digits of ZIP code | `01037` | No |
| `geolocation_lat` | `DOUBLE` | Latitude coordinate | `-23.545621` | No |
| `geolocation_lng` | `DOUBLE` | Longitude coordinate | `-46.639292` | No |
| `geolocation_city` | `STRING` | City name for this ZIP | `são paulo` | No |
| `geolocation_state` | `STRING` | 2-letter state code | `SP` | No |

#### Data Quality Notes

- **261,831 duplicates** are expected and documented — they reflect the reality of Brazilian ZIP geography, not ingestion errors.
- Some latitude/longitude values are slightly outside Brazilian territory (data entry errors or edge cases near borders). Filter using bounding box: lat ∈ [-34, 5], lng ∈ [-74, -28].
- City name spelling varies across rows for the same ZIP — this is the source of the inconsistency in `customers.customer_city` and `sellers.seller_city`.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Full raw load — retain all rows. Partition by `geolocation_state` for performance. |
| **Silver** | Deduplicate: keep first row per `geolocation_zip_code_prefix`. Apply bounding box filter. Join to customers and sellers to enrich with lat/lng. |
| **Gold / dbt** | `dim_geography` dimension table. Used in `dim_customers` and `dim_sellers` via surrogate key. |
| **Power BI** | Customer and seller heat maps. Geographic drill-down in sales dashboards. |
| **Machine Learning** | Haversine distance between seller and customer ZIP centroids → delivery time prediction feature. |

---

### 🌐 Table: `product_category_translation`

#### Purpose
A simple reference table mapping 71 Portuguese product category names to their English equivalents. Essential for producing English-language dashboards and reports from the Portuguese-native `products` table.

#### Business Questions Supported
- (Reference only — enables business-readable category names in all downstream uses)

#### Dataset Statistics

| Metric | Value |
|---|---|
| **Rows** | 71 |
| **Columns** | 2 |
| **Null Values** | 0 |
| **Coverage** | 71 of 74 Portuguese category names in `products` |

#### Granularity
One row represents one product category name mapping.

#### Primary Key
`product_category_name` (Portuguese)

#### Foreign Keys
Referenced by: `products.product_category_name`

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `product_category_name` | `STRING` | Original Portuguese category name | `cama_mesa_banho` | No |
| `product_category_name_english` | `STRING` | English translation | `bed_bath_table` | No |

#### Data Quality Notes

- **3 Portuguese category names** in `products` do not have a matching row in this table. These are: `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`, and one unlabelled category. Resolve in Silver using a manual mapping supplemented by custom translations (the EDA notebook applied custom translations for readability).
- The provided English translations use underscores (`bed_bath_table`). For display purposes in dashboards, replace underscores with spaces and apply title casing: `Bed Bath & Table`.

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Loaded as a small reference table. |
| **Silver** | Joined to `products` to add `category_name_en`. Add manual overrides for 3 unmapped categories. Apply display formatting (spaces, title case). |
| **Gold / dbt** | Embedded in `dim_products` as `category_en` attribute. Optionally modelled as `dim_category` if a category hierarchy is introduced. |
| **Power BI** | Display field in all product and category visuals. Slicer filter on category. |
| **Machine Learning** | Category encoded as a categorical feature after joining to order items. |

---

## Entity Relationship Summary

The following matrix describes the relationships between core entities. Arrow direction indicates the cardinality: `→` means "one to many."

```
┌──────────────┐         ┌─────────────┐         ┌──────────────┐
│  customers   │ 1 ───► N│   orders    │ 1 ───► N│ order_items  │
│              │         │             │         │              │
│ customer_id  │─────────│ customer_id │         │ order_id     │
└──────────────┘         │ order_id    │────┬────│ product_id   │
                         └─────────────┘    │    │ seller_id    │
                               │            │    └──────────────┘
                         ┌─────┴──────┐     │           │
                    ┌────┤            ├─┐   │           │
                    │    │ 1        1 │ │   │    ┌──────┘    ┌──────────┐
              ┌─────▼──┐ └────────────┘ │   │    │           │ sellers  │
              │order_  │                │   └────▼──────┐    │          │
              │payments│          ┌─────▼─┐ │ products  │    │seller_id │
              │        │          │order_ │ │           │    └──────────┘
              └────────┘          │reviews│ │product_id │
                                  └───────┘ └───────────┘
                                                  │
                                     ┌────────────▼────────────┐
                                     │ product_category_        │
                                     │ translation              │
                                     └──────────────────────────┘

customers, sellers ←──── geolocation (via zip_code_prefix)
```

### Relationship Matrix

| From | To | Join Key | Type | Notes |
|---|---|---|---|---|
| `customers` | `orders` | `customer_id` | 1:N | One customer → many orders (use `customer_unique_id` for true customer count) |
| `orders` | `order_items` | `order_id` | 1:N | One order → 1–21 items |
| `orders` | `order_payments` | `order_id` | 1:N | One order → 1–N payment methods |
| `orders` | `order_reviews` | `order_id` | 1:1 (≈) | One order → one review (deduplicate on latest) |
| `order_items` | `products` | `product_id` | N:1 | Many items → one product SKU |
| `order_items` | `sellers` | `seller_id` | N:1 | Many items → one seller |
| `products` | `product_category_translation` | `product_category_name` | N:1 | Many products → one category |
| `customers` | `geolocation` | `customer_zip_code_prefix` | N:1 | Many customers → one ZIP centroid |
| `sellers` | `geolocation` | `seller_zip_code_prefix` | N:1 | Many sellers → one ZIP centroid |

---

## Medallion Architecture Mapping

### Bronze Layer — Raw Ingestion

| Table | Ingestion Method | Format | Partition | Special Handling |
|---|---|---|---|---|
| `customers` | Kafka batch / ADF | Delta Lake | `customer_state` | None |
| `orders` | Kafka batch / ADF | Delta Lake | `order_purchase_year`, `order_purchase_month` | Timestamp strings — do not cast yet |
| `order_items` | Kafka batch / ADF | Delta Lake | `shipping_limit_year` | None |
| `order_payments` | Kafka batch / ADF | Delta Lake | `order_id` (hash bucket) | None |
| `order_reviews` | Kafka batch / ADF | Delta Lake | `review_creation_year` | Preserve raw Portuguese text |
| `products` | ADF (small table) | Delta Lake | `product_category_name` | None |
| `sellers` | ADF (small table) | Delta Lake | `seller_state` | None |
| `geolocation` | ADF (large table) | Delta Lake | `geolocation_state` | Full load — 1M rows, do not stream |
| `product_category_translation` | ADF (reference) | Delta Lake | None | Static — load once |

### Silver Layer — Cleansed and Enriched

| Table | Key Transformations | Output Table |
|---|---|---|
| `customers` | Title-case city names, join geolocation for lat/lng | `silver_customers` |
| `orders` | Cast timestamps, impute carrier dates, remove corrupt records, derive duration columns, derive `is_late` flag | `silver_orders` |
| `order_items` | Cast price/freight to DECIMAL, derive `item_total`, validate `price > 0` | `silver_order_items` |
| `order_payments` | Aggregate per order, derive `has_voucher`, `max_installments`, `payment_method_count` | `silver_order_payments` |
| `order_reviews` | Deduplicate, derive `review_sentiment`, compute `hours_to_review`, handle null text | `silver_order_reviews` |
| `products` | Join category translation, impute null categories, compute `product_volume_cm3` | `silver_products` |
| `sellers` | City name standardisation, ZIP → lat/lng enrichment | `silver_sellers` |
| `geolocation` | **Deduplicate** to one row per ZIP prefix, apply coordinate bounding box | `silver_geolocation` |
| `product_category_translation` | Add display formatting (spaces, title case), resolve 3 unmapped categories | `silver_category_lookup` |

### Gold Layer — dbt Models & Warehouse Targets

| dbt Model | Source Tables | Warehouse Target | Purpose |
|---|---|---|---|
| `dim_customers` | `silver_customers`, `silver_geolocation` | `fabric_dw.dim_customers` | Customer dimension with geography |
| `dim_products` | `silver_products`, `silver_category_lookup` | `fabric_dw.dim_products` | Product dimension with English category |
| `dim_sellers` | `silver_sellers`, `silver_geolocation` | `fabric_dw.dim_sellers` | Seller dimension with location |
| `dim_date` | Generated (date spine) | `fabric_dw.dim_date` | Calendar dimension (day to year) |
| `dim_geography` | `silver_geolocation` | `fabric_dw.dim_geography` | State/city reference for maps |
| `dim_payment_method` | `silver_order_payments` | `fabric_dw.dim_payment_method` | Payment type reference |
| `fact_sales` | `silver_order_items`, `silver_orders`, `silver_order_payments` | `fabric_dw.fact_sales` | Core revenue fact table |
| `fact_deliveries` | `silver_orders` | `fabric_dw.fact_deliveries` | Delivery performance fact table |
| `fact_reviews` | `silver_order_reviews`, `silver_orders` | `fabric_dw.fact_reviews` | Customer satisfaction fact table |
| `ml_features_churn` | Multiple silver tables | `fabric_dw.ml_features_churn` | RFM + delivery + sentiment features for churn model |
| `ml_features_demand` | `silver_order_items`, `silver_orders` | `fabric_dw.ml_features_demand` | Category-level time series for forecasting |

---

## Data Engineering Considerations

### Partitioning Strategy

| Table | Recommended Partition Key | Rationale |
|---|---|---|
| `orders` | `year(order_purchase_timestamp)`, `month(order_purchase_timestamp)` | Primary time-series analytics pattern. Enables partition pruning on date-range queries. |
| `order_items` | `year(shipping_limit_date)` | Aligns with order partitioning. Enables seller performance queries by period. |
| `order_reviews` | `year(review_creation_date)` | Sentiment trend analysis by time window. |
| `geolocation` | `geolocation_state` | Geographic drill-down queries. Reduces scan for regional analyses. |
| `fact_sales` (Fabric DWH) | `order_year`, `order_month` + hash distribute on `customer_id` | Balances time-range query pruning with join performance on customer dimension. |

### Indexing Recommendations (Microsoft Fabric Warehouse)

| Table | Index Type | Column(s) | Rationale |
|---|---|---|---|
| `fact_sales` | Clustered Columnstore | All columns | Default for large fact tables — enables compression and vectorised scan. |
| `dim_customers` | Replicated | All columns | Small dimension (99K rows) — replicate to avoid shuffle on joins. |
| `dim_products` | Replicated | All columns | Small dimension (33K rows). |
| `dim_date` | Replicated | All columns | Tiny table (~1K rows). Never distributed. |
| `dim_sellers` | Replicated | All columns | Very small (3K rows). |
| `fact_deliveries` | Clustered Columnstore | Hash on `order_id` | Join-heavy table — hash distribution reduces data movement. |

### Incremental Loading Strategy

> **📌 Note:** The Olist dataset is a historical snapshot — true incremental loading is not applicable to the raw data. However, the pipeline should be designed to support incremental patterns for when real-time order feeds are connected in production.

| Pattern | Application |
|---|---|
| **Full load (one-time)** | `geolocation`, `product_category_translation`, `products`, `sellers` — reference tables that change rarely. |
| **Append-only incremental** | `orders`, `order_items`, `order_payments`, `order_reviews` — new records only, keyed on `order_id`. |
| **CDC (production target)** | Use watermark column (`order_purchase_timestamp` for orders, `review_creation_date` for reviews) for incremental Bronze loads when connected to a live data source. |
| **SCD Type 2 (future)** | Apply to `dim_customers` and `dim_products` if product pricing or customer location changes need historical tracking. |

### Data Quality Risks

| Risk | Affected Table(s) | Severity | Mitigation |
|---|---|---|---|
| Geolocation fan-out joins | `geolocation` | 🔴 High | Deduplicate in Silver before any join. Add dbt test: assert `COUNT(*) = COUNT(DISTINCT zip_prefix)` |
| Null delivery timestamps on delivered orders | `orders` | 🔴 High | Apply business-logic null handling. Flag anomalous records. Run Great Expectations suite. |
| Multi-payment join duplication | `order_payments` | 🔴 High | Always aggregate payments by `order_id` before joining to orders. Add dbt test: assert no order-level duplicates after aggregation. |
| Portuguese text in NLP pipeline | `order_reviews` | 🟡 Medium | Use Portuguese-capable NLP libraries. Test tokenisation on a sample before full run. |
| Unmapped product categories | `products` | 🟡 Medium | Manual override mapping for 3 unmapped categories. Validate coverage in Silver dbt test. |
| Negative computed durations | `orders` | 🟡 Medium | Set to 0, flag records. Do not drop — orders are valid, timestamps are unreliable. |
| City name inconsistencies | `customers`, `sellers` | 🟢 Low | Standardise with title-case function in Silver. Not analytically critical. |

### Performance Considerations

- The **`geolocation` table at 1M rows** is the largest in the dataset. Avoid broadcasting it in Spark joins. Join after deduplication (738K rows post-Silver).
- The **master transactional dataset** (all tables joined) produces ~119K rows. This is small enough for Pandas; using PySpark is for skills demonstration and future scalability, not current necessity.
- **Payment aggregation before join** is mandatory. Failing to aggregate first expands `orders` from 99K to 103K rows — a subtle fan-out that inflates revenue metrics by ~4.5%.
- In Fabric Warehouse, use **serverless SQL pools** for ad-hoc queries during development. Reserve dedicated SQL pools for scheduled production reports.

---

## Key Insights from Profiling

### Major Data Quality Findings

| Finding | Table | Action Required |
|---|---|---|
| 261,831 duplicate geolocation rows | `geolocation` | Deduplicate in Silver — mandatory before any join |
| 2 corrupt "delivered" orders with no delivery dates | `orders` | Remove from Silver — cannot be imputed |
| 1,603 negative waiting-time anomalies | `orders` | Set to 0, flag records, document assumption |
| ~58% of reviews have no text | `order_reviews` | Handle empty strings in NLP pipeline; retain records for star-score analysis |
| 3 unmapped product categories | `products` + `translation` | Apply manual category override in Silver |
| Multiple payment rows per order | `order_payments` | Aggregate before joining — critical pipeline correctness issue |

### Table Size Reference

| Table | Rows | Size Category |
|---|---|---|
| `geolocation` | 1,000,163 | 🔴 Large |
| `order_items` | 112,650 | 🟡 Medium |
| `order_payments` | 103,886 | 🟡 Medium |
| `orders` | 99,441 | 🟡 Medium |
| `customers` | 99,441 | 🟡 Medium |
| `order_reviews` | 99,224 | 🟡 Medium |
| `products` | 32,951 | 🟢 Small |
| `sellers` | 3,095 | 🟢 Small |
| `product_category_translation` | 71 | 🟢 Tiny |

### Tables Requiring Special Handling

1. **`geolocation`** — Deduplicate before use. Never join raw. Largest table by 10x.
2. **`order_payments`** — Aggregate by `order_id` before joining. Raw table has multiple rows per order.
3. **`orders`** — Complex null handling with business logic. Two records must be removed. Timestamp imputation required.
4. **`order_reviews`** — Portuguese NLP. ~59% null text fields. Requires multilingual NLP toolkit.
5. **`products`** — 3 unmapped categories and 610 null category names. Requires manual mapping override.

### Business Significance

The Olist dataset tells a clear and commercially relevant story:

- **Retention is the central problem.** Only 3% of customers return for a second order — an order of magnitude below healthy e-commerce benchmarks. This is the primary justification for the churn prediction ML model.
- **Delivery is the primary satisfaction driver.** 67% of 1-star reviews mention delivery problems. A late delivery is statistically 4× more likely to produce a bad review (chi-square p < 0.001). Improving logistics has a higher expected ROI than improving product quality.
- **Payment flexibility matters.** 50% of credit card transactions use instalments. Instalment orders have significantly higher AOV. In Brazil's emerging market context, payment flexibility is a growth lever, not a convenience feature.
- **Geographic concentration creates risk.** 63% of orders originate from the São Paulo–Rio de Janeiro–Minas Gerais corridor. Seller concentration in São Paulo (≈70%) means northern Brazil faces consistently longer delivery times — a structural satisfaction problem.
- **Cross-selling opportunity is untapped.** 88% of orders contain a single item. Customers who buy 4+ items spend 4.6× more than single-item buyers. A product recommendation system targeting multi-item basket growth has a quantifiable revenue upside.

> **💡 Tip:** When presenting this dataset in design reviews or stakeholder meetings, lead with the 3% retention rate and the 4× late-delivery bad-review multiplier. These two numbers justify the entire analytical platform and the ML investment in a single sentence.

---

*Document generated for the Olist E-Commerce Intelligence Platform · Data Engineering Team · v1.0.0*

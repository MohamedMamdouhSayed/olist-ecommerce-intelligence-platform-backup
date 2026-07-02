# 📚 Olist E-Commerce Intelligence Platform
## Data Dictionary

---

| Field | Detail |
|---|---|
| **Project Name** | Olist E-Commerce Intelligence Platform |
| **Dataset Name** | Brazilian E-Commerce Public Dataset by Olist |
| **Document Version** | v1.0.0 |
| **Authors** | Mohamed Mamdouh · Christen Nashat · Tasbeeh Ahmed · Martina Farah · Mai Ahmed · Alaa Ramadan |
| **Last Updated** | July 2025 |
| **Status** | ✅ Active |
| **Purpose** | Single source of truth for all data definitions, lineage, quality contracts, and downstream usage across the platform's Bronze → Silver → Gold pipeline, Microsoft Fabric Warehouse, Power BI dashboards, FastAPI services, and Machine Learning models. |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Dataset Overview](#2-dataset-overview)
3. [Detailed Table Documentation](#3-detailed-table-documentation)
   - [customers](#-table-customers)
   - [orders](#-table-orders)
   - [order_items](#-table-order_items)
   - [order_payments](#-table-order_payments)
   - [order_reviews](#-table-order_reviews)
   - [products](#-table-products)
   - [sellers](#-table-sellers)
   - [geolocation](#-table-geolocation)
   - [product_category_translation](#-table-product_category_translation)
4. [Relationship Matrix](#4-relationship-matrix)
5. [Data Engineering Notes](#5-data-engineering-notes)
6. [Business Glossary](#6-business-glossary)
7. [Final Summary](#7-final-summary)

---

## 1. Executive Summary

### What is the Olist Dataset?

The **Brazilian E-Commerce Public Dataset by Olist** is a real-world, anonymised transactional dataset released publicly by Olist — Brazil's largest online marketplace aggregator. It captures the complete customer purchasing journey across approximately **100,000 orders** placed between **September 2016 and October 2018**, spanning order lifecycle management, multi-method payments, logistics performance, seller operations, product cataloguing, and customer satisfaction surveys submitted in Brazilian Portuguese.

The dataset encompasses 9 interrelated tables totalling **~1.55 million rows** across all entities. Its structure reflects a genuine multi-sided marketplace: customers place orders fulfilled by independent sellers, shipped via third-party carriers, and reviewed post-delivery. This architecture makes it analytically representative of any modern e-commerce platform.

### Why This Dataset Matters

This dataset is valuable precisely because it is messy in realistic ways: it contains null delivery timestamps, referential edge cases, geolocation fan-out duplicates, Portuguese-language free-text reviews, and a critically low repeat purchase rate of 3%. These characteristics mirror the data quality challenges faced by real data engineering teams at scale.

Two numbers summarise the platform's business case:

- **3% repeat customer rate** — an order of magnitude below healthy e-commerce benchmarks, justifying the investment in churn prediction models and retention analytics.
- **4× bad-review multiplier on late deliveries** — statistically significant (chi-square p < 0.001), making delivery performance the single highest-ROI improvement opportunity on the platform.

### How It Supports the Intelligence Platform

| Workload | Dataset Contribution |
|---|---|
| **Analytics & BI** | Sales trends, delivery KPIs, category performance, geographic distribution |
| **Business Intelligence** | Star Schema dimensional model powering Power BI dashboards |
| **Machine Learning** | RFM churn features, time-series demand forecasting, Portuguese NLP sentiment |
| **Operational Reporting** | Seller performance scorecards, payment method analysis, on-time delivery rate |

### Who Uses This Document

| Role | Primary Use |
|---|---|
| **Data Engineer** | Pipeline design, Bronze/Silver/Gold transformation contracts, data quality rules |
| **Data Analyst** | Column semantics, business definitions, KPI logic, join keys |
| **BI Developer** | Dimension and fact table structure, Power BI field descriptions |
| **ML Engineer** | Feature engineering inputs, label definitions, training dataset construction |
| **Data Architect** | Relationship matrix, partitioning strategy, storage format decisions |

---

## 2. Dataset Overview

| Table | Description | Rows | Columns | Grain |
|---|---|---|---|---|
| `customers` | Customer identity and geographic location | 99,441 | 5 | One row per customer-order context |
| `orders` | Full order lifecycle from placement to delivery | 99,441 | 8 | One row per order |
| `order_items` | Individual line items within each order | 112,650 | 7 | One row per product per order |
| `order_payments` | Payment transactions associated with each order | 103,886 | 5 | One row per payment method per order |
| `order_reviews` | Customer satisfaction surveys submitted post-delivery | 99,224 | 7 | One row per review |
| `products` | Product catalogue with physical attributes and category | 32,951 | 9 | One row per product SKU |
| `sellers` | Seller profiles and geographic location | 3,095 | 4 | One row per seller |
| `geolocation` | Brazilian ZIP code prefix to coordinate mapping | 1,000,163 | 5 | One row per ZIP + lat/lng pair (pre-dedup) |
| `product_category_translation` | Portuguese to English category name mapping | 71 | 2 | One row per category |

> **Total raw records across all tables:** ~1,551,021 rows

---

## 3. Detailed Table Documentation

---

### 👤 Table: `customers`

#### Purpose

Stores the unique identity and geographic location of each customer. Because Olist uses a pseudonymisation strategy, `customer_id` is **scoped per order** — a single physical customer who places two orders will appear as two records with different `customer_id` values. The true customer identifier across orders is `customer_unique_id`.

#### Business Importance

This table is the entry point for all customer-facing analytics. It enables geographic market analysis, customer acquisition tracking, and — via `customer_unique_id` — the computation of true retention and repeat purchase metrics. The distinction between the two customer key columns is the most common source of analytical errors on this platform.

#### Granularity

One row represents one customer **per order context**. A physical customer who placed 3 orders will have 3 `customer_id` values, all sharing the same `customer_unique_id`.

#### Primary Key

`customer_id`

#### Foreign Keys

Referenced by: `orders.customer_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `orders` | `customer_id` | 1:N | One customer context → one or more orders |
| `geolocation` | `customer_zip_code_prefix` | N:1 | Many customers → one ZIP centroid (after dedup) |

#### Business Questions Supported

- How many unique physical customers does Olist serve? *(requires `customer_unique_id`)*
- What is the geographic distribution of customers across Brazilian states and cities?
- Which cities and states generate the highest order volumes?
- What is the true repeat purchase rate across the platform?
- Which customer cohorts show the highest lifetime value?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `customer_id` | `STRING` | Order-scoped pseudonymised customer identifier. Unique per order — not suitable for counting physical customers. | `06b8999e2fba1a1fbc88172c00ba8bc7` | No |
| `customer_unique_id` | `STRING` | True cross-order customer identifier. Use this column to track repeat purchases and customer lifetime behaviour. | `861eff4711a542e4b93843c6dd7febb0` | No |
| `customer_zip_code_prefix` | `STRING` | First 5 digits of the Brazilian 8-digit CEP (postal code). Used to join with `geolocation` for lat/lng enrichment. | `14409` | No |
| `customer_city` | `STRING` | City name in which the customer resides. Stored in inconsistent lowercase in the raw source. | `franca` | No |
| `customer_state` | `STRING` | Two-letter Brazilian state code (IBGE standard). | `SP` | No |

#### Data Quality Considerations

| Issue | Detail | Handling Strategy |
|---|---|---|
| City name casing | All city names stored in lowercase; some with accented characters stripped | Standardise to title case with accent normalisation in Silver (`franca` → `Franca`) |
| `customer_id` vs `customer_unique_id` trap | 3,345 customers have placed more than one order (3.0% repeat rate). Joining on `customer_id` counts orders, not customers | Document which key is used in every downstream model; enforce via dbt column descriptions |
| No nulls | No missing values detected across any column | No imputation required |
| Geolocation mismatch | Some ZIP prefixes in `customers` do not appear in `geolocation` — coverage is not 100% | Handle with LEFT JOIN; null coordinates are acceptable for non-map analytics |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Ingested as-is from CSV. Schema enforced via Delta Lake. No transformations applied. |
| **Silver** | City name standardised (title case, accent normalisation). ZIP code joined to `silver_geolocation` to enrich with latitude, longitude, and state region. |
| **Gold / dbt** | `dim_customers` dimension table in the star schema. Surrogate key generated. SCD Type 2 not applicable to this static snapshot dataset. |
| **Fabric Warehouse** | Replicated distribution (99K rows — small enough to broadcast across all query nodes). |
| **Power BI** | Customer geographic distribution filled map by state. City-level drill-down filter. Customer count KPI tile. |
| **Machine Learning** | `customer_unique_id` used as the grouping key to aggregate RFM (Recency, Frequency, Monetary) features for the churn prediction model. `customer_state` used as a categorical geographic feature. |

---

### 📦 Table: `orders`

#### Purpose

The central entity of the Olist dataset. Records the complete lifecycle of each order from creation through payment approval, carrier handoff, and final customer delivery. Contains five timestamp columns that together enable detailed delivery performance analysis and SLA measurement.

#### Business Importance

Every analytical and ML workload on this platform traces back to this table. It is the hub of the star schema, the time-series index for demand forecasting, and the source of the most powerful predictive signal in the dataset: `is_late`. Null handling in this table is the most complex data quality challenge in the entire pipeline.

#### Granularity

One row represents one order. An order may contain multiple items (see `order_items`) and multiple payment methods (see `order_payments`).

#### Primary Key

`order_id`

#### Foreign Keys

- `customer_id` → `customers.customer_id`
- Referenced by: `order_items.order_id`, `order_payments.order_id`, `order_reviews.order_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `customers` | `customer_id` | N:1 | Many orders → one customer context |
| `order_items` | `order_id` | 1:N | One order → 1 to 21 line items |
| `order_payments` | `order_id` | 1:N | One order → 1 to N payment methods |
| `order_reviews` | `order_id` | 1:1 (≈) | One order → one review (deduplicate on latest) |

#### Business Questions Supported

- What is the overall order volume trend from 2016 to 2018?
- What percentage of orders are delivered on time vs late?
- What is the average approval time, shipping time, and end-to-end delivery time?
- How many orders were cancelled, and at what stage in the lifecycle?
- Which months and seasons show the highest order volumes?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `order_id` | `STRING` | Unique order identifier. Primary key for all order-level analytics. | `e481f51cbdc54678b7cc49136f2d6af7` | No |
| `customer_id` | `STRING` | Order-scoped customer reference. Foreign key to `customers`. | `9ef432eb6251297304e76186b10a928d` | No |
| `order_status` | `STRING` | Current status in the order lifecycle. Values: `delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing`, `created`, `approved`. | `delivered` | No |
| `order_purchase_timestamp` | `TIMESTAMP` | Moment the customer submitted the order. Primary time dimension for all trend analysis. | `2017-10-02 10:56:33` | No |
| `order_approved_at` | `TIMESTAMP` | Moment payment was confirmed by the payment processor. Null for cancelled and some corrupted orders. | `2017-10-02 11:07:15` | Yes |
| `order_delivered_carrier_date` | `TIMESTAMP` | Moment the seller handed the package to the logistics carrier. Null for non-delivered orders and some data anomalies. | `2017-10-04 19:55:00` | Yes |
| `order_delivered_customer_date` | `TIMESTAMP` | Moment the customer received the package. Null for orders not yet delivered at dataset cutoff. | `2017-10-10 21:25:13` | Yes |
| `order_estimated_delivery_date` | `TIMESTAMP` | Estimated delivery date displayed to the customer at time of purchase. Non-null for all orders. Used to compute `is_late`. | `2017-10-18 00:00:00` | No |

#### Derived Columns (Silver Layer)

| Derived Column | Formula | Purpose |
|---|---|---|
| `approval_time_hrs` | `(order_approved_at - order_purchase_timestamp) / 3600` | Payment processing speed |
| `waiting_time_days` | `(order_delivered_carrier_date - order_approved_at) / 86400` | Seller pick-and-pack time |
| `shipping_time_days` | `(order_delivered_customer_date - order_delivered_carrier_date) / 86400` | Carrier transit time |
| `total_delivery_days` | `(order_delivered_customer_date - order_purchase_timestamp) / 86400` | End-to-end fulfilment time |
| `is_late` | `order_delivered_customer_date > order_estimated_delivery_date` | Binary flag; primary delivery KPI and churn signal |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| 2 corrupt `delivered` orders with no timestamps | 🔴 Critical | Orders marked `delivered` but all 5 timestamp columns are NULL. Cannot be imputed. | Remove in Silver. Document removed `order_id` values. |
| 160 null `order_approved_at` | 🟠 High | Breakdown: 141 cancelled, 14 delivered (corruption), 5 in limbo state | Apply business-logic null handling; do not blanket-impute |
| 1,783 null `order_delivered_carrier_date` | 🟠 High | Majority are non-delivered orders (shipped, cancelled) | Null is valid for non-delivered; impute only where `customer_date` is present |
| 2,965 null `order_delivered_customer_date` | 🟠 High | Orders not yet delivered at dataset cutoff or cancelled | Expected nulls; handle in `is_late` logic to avoid false positives |
| 1,603 negative `waiting_time_days` | 🟡 Medium | `carrier_date < approval_date` — caused by timezone inconsistencies | Set computed duration to 0; flag record with `is_anomalous = TRUE` |
| 67 negative `shipping_time_days` | 🟡 Medium | Same root cause as above | Same handling: set to 0, flag |
| Imputation for carrier date | 🟡 Medium | Where `customer_date` is known but `carrier_date` is null | Impute as `customer_date - 3 days` (observed median transit lag). Document assumption in dbt model header. |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Full CSV load. All timestamps stored as strings — do not cast in Bronze. Append-only Delta table partitioned by `order_purchase_year` and `order_purchase_month`. |
| **Silver** | Cast all 5 timestamp columns from STRING to TIMESTAMP. Apply null imputation rules as documented above. Remove 2 corrupt records. Compute all 5 derived columns. Derive `is_late` boolean flag. |
| **Gold / dbt** | Central to both `fact_sales` and `fact_deliveries`. `is_late` drives delivery performance KPIs. `order_purchase_timestamp` provides the date dimension join key via `dim_date`. |
| **Fabric Warehouse** | Hash distributed on `order_id`. Clustered columnstore index. Partitioned by `order_year`, `order_month`. |
| **Power BI** | Delivery performance dashboard. On-time rate trend over time. Order status funnel. Monthly order volume bar chart. |
| **Machine Learning** | Churn: `is_late`, `total_delivery_days`, `approval_time_hrs` as features. Demand: `order_purchase_timestamp` as time series index. NLP: joined to `order_reviews` to link sentiment with delivery performance. |

---

### 🛒 Table: `order_items`

#### Purpose

Records the individual line items within each order — one row per product per order. This is the most granular transactional table in the dataset and the foundation for all revenue, product performance, and seller analytics.

#### Business Importance

`order_items` holds the price and freight value columns that are the source of truth for revenue measurement at the product and seller level. It is also the bridge entity connecting orders to products and sellers, making it the most join-intensive table in the star schema.

> **⚠️ Aggregation Note:** For order-level revenue, use `SUM(payment_value)` from `order_payments`. For product-level revenue, use `SUM(price + freight_value)` from this table. The two totals will not match exactly due to voucher discounts applied at the order level.

#### Granularity

One row represents one product SKU within one order. An order containing 3 different products will have 3 rows in this table.

#### Primary Key

`(order_id, order_item_id)` — composite key

#### Foreign Keys

- `order_id` → `orders.order_id`
- `product_id` → `products.product_id`
- `seller_id` → `sellers.seller_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `orders` | `order_id` | N:1 | Many items → one parent order |
| `products` | `product_id` | N:1 | Many line items → one product SKU |
| `sellers` | `seller_id` | N:1 | Many line items → one seller |

#### Business Questions Supported

- What is the total revenue per product category?
- Which sellers generate the highest sales volume and revenue?
- What is the average freight cost relative to product price?
- How many items are typically purchased in a single order?
- What is the basket size distribution across all orders?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `order_id` | `STRING` | Parent order reference. Foreign key to `orders`. | `00010242fe8c5a6d1ba2dd792cb16214` | No |
| `order_item_id` | `INTEGER` | Sequential item number within the order (1 = first item). Part of the composite primary key. | `1` | No |
| `product_id` | `STRING` | Product SKU reference. Foreign key to `products`. | `4244733e06e7ecb4970a6e2683c13e61` | No |
| `seller_id` | `STRING` | Seller reference for this line item. Foreign key to `sellers`. | `48436dade18ac8b2bce089ec2a041202` | No |
| `shipping_limit_date` | `TIMESTAMP` | Deadline by which the seller must hand the package to the carrier. Used for seller SLA compliance. | `2017-09-19 09:45:35` | No |
| `price` | `DECIMAL(10,2)` | Item price in Brazilian Reais (R$) at time of purchase. Excludes freight. | `58.90` | No |
| `freight_value` | `DECIMAL(10,2)` | Freight cost charged for this item in R$. In multi-item orders, freight is split across items. | `13.29` | No |

#### Derived Columns (Silver Layer)

| Derived Column | Formula | Purpose |
|---|---|---|
| `item_total` | `price + freight_value` | Gross revenue per line item including shipping |
| `freight_ratio` | `freight_value / price` | Freight as a proportion of item price; used to identify high-shipping-cost categories |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| Multi-item freight split | 🟠 High | In orders with multiple items, `freight_value` is split proportionally across items — summing across items gives correct total | Always aggregate at order level when comparing to `order_payments.payment_value` |
| `price = 0` records | 🟡 Medium | A small number of records have zero price (gift items, test orders) | Flag in Silver; exclude from revenue aggregations but retain for order count metrics |
| `shipping_limit_date` precision | 🟢 Low | Timestamps are reliable but reflect seller SLA, not actual carrier pickup | Do not confuse with `order_delivered_carrier_date` in `orders` |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw CSV load. `price` and `freight_value` stored as strings — cast to DECIMAL in Silver. |
| **Silver** | Cast price columns to `DECIMAL(10,2)`. Validate `price > 0`. Derive `item_total` and `freight_ratio`. |
| **Gold / dbt** | Core measure table feeding `fact_sales`. `price` and `freight_value` as measures. Joins to `dim_products`, `dim_sellers`, `dim_customers` (via orders). |
| **Fabric Warehouse** | Hash distributed on `order_id`. Clustered columnstore index. Partitioned by `shipping_limit_year`. |
| **Power BI** | Revenue by category, seller, and state. Basket size distribution. Freight cost analysis. Top products by revenue. |
| **Machine Learning** | Demand: `category`, `avg_price`, order counts by time period. Churn: `total_spend`, `avg_order_value`, `items_per_order` as RFM proxy features. |

---

### 💳 Table: `order_payments`

#### Purpose

Records all payment transactions associated with each order. A single order may be paid using multiple payment methods (e.g., partial voucher + credit card), resulting in multiple rows per order. This table is the source of truth for payment behaviour analytics.

#### Business Importance

Payment method mix and instalment behaviour are significant market-specific signals in the Brazilian e-commerce context. In Brazil, credit card instalments are a primary driver of high-value purchases. This table enables payment flexibility analysis, voucher discount impact assessment, and instalment-as-a-feature engineering for ML models.

#### Granularity

One row represents one payment method used within one order. An order paid by credit card and a voucher simultaneously will have 2 rows.

#### Primary Key

`(order_id, payment_sequential)` — composite key

#### Foreign Keys

- `order_id` → `orders.order_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `orders` | `order_id` | N:1 | Many payment rows → one parent order |

#### Business Questions Supported

- What is the payment method mix across all orders?
- What percentage of credit card payments use instalments?
- How does average order value differ across payment methods?
- What is the impact of voucher discounts on net revenue?
- Do high-instalment customers have higher or lower churn rates?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `order_id` | `STRING` | Parent order reference. Foreign key to `orders`. | `b81ef226f3fe1789b1e8b2acac839d17` | No |
| `payment_sequential` | `INTEGER` | Position of this payment method in the payment sequence (1 = primary method). | `1` | No |
| `payment_type` | `STRING` | Payment method used. Values: `credit_card`, `boleto`, `voucher`, `debit_card`, `not_defined`. | `credit_card` | No |
| `payment_installments` | `INTEGER` | Number of monthly instalments elected by the customer. 1 = upfront payment. Max observed: 24. | `3` | No |
| `payment_value` | `DECIMAL(10,2)` | Amount charged through this payment method in R$. For vouchers, this is the discount value applied. | `99.33` | No |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| Fan-out join without aggregation | 🔴 Critical | Joining directly to `orders` without aggregating first increases row count from 99,441 to 103,886 — inflating revenue by ~4.5% | Always `GROUP BY order_id, SUM(payment_value)` before joining to any order-level table. Enforce via dbt test. |
| `payment_type = 'not_defined'` | 🟡 Medium | 3 records with undefined payment method | Exclude from payment method analysis; retain for revenue totals |
| Voucher value semantics | 🟡 Medium | For `payment_type = 'voucher'`, `payment_value` is a discount amount, not a gross payment | Account for voucher rows when computing net revenue: `SUM(payment_value) WHERE payment_type != 'voucher'` gives gross; include for total charged |
| Instalment distribution | 🟢 Low | 50.1% of credit card orders use instalments; high-instalment orders (6–24x) correlate with high AOV | Document as a feature, not a data quality issue; use `max_installments` as ML feature |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw load. All columns exact. No transformations. |
| **Silver** | Aggregate per `order_id`. Derive: `total_payment_value` (SUM), `has_voucher` (BOOLEAN), `max_installments`, `payment_method_count`, `primary_payment_type` (at `payment_sequential = 1`). |
| **Gold / dbt** | `dim_payment_method` dimension (credit_card, boleto, voucher, debit_card). `payment_value` as measure on `fact_sales`. |
| **Fabric Warehouse** | Aggregated to order level before loading. Hash distributed on `order_id`. |
| **Power BI** | Payment method mix donut chart. Instalment distribution histogram. Voucher usage KPI. |
| **Machine Learning** | Churn: `primary_payment_type`, `max_installments`, `has_voucher` as customer financial behaviour features. Instalment depth as a proxy for customer price sensitivity. |

---

### ⭐ Table: `order_reviews`

#### Purpose

Captures customer satisfaction feedback submitted after order delivery. Each review includes a 1–5 star score and optional free-text comments in **Brazilian Portuguese**. This table is the sole source for NLP analysis and the primary source for customer sentiment scoring.

#### Business Importance

Reviews are the voice of the customer. The `review_score` column is simultaneously a customer satisfaction KPI, a churn prediction signal, and an NLP training label. The statistical finding that late deliveries produce a 4× higher probability of a 1-star review makes this table central to the platform's core business narrative: **fix logistics, fix reviews, fix retention**.

#### Granularity

One row represents one customer review for one order. In rare cases, a single order has more than one review — deduplicate by retaining the latest `review_creation_date` per `order_id`.

#### Primary Key

`review_id`

#### Foreign Keys

- `order_id` → `orders.order_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `orders` | `order_id` | N:1 | Many reviews → one parent order (deduplicate first) |

#### Business Questions Supported

- What is the platform's average review score and how has it trended over time?
- Which product categories and sellers generate the most negative reviews?
- What percentage of orders with late delivery receive 1-star reviews?
- What are the most common complaint topics in negative Portuguese-language reviews?
- How quickly do customers submit reviews after delivery?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `review_id` | `STRING` | Unique review identifier. | `7bc2406110b926393aa56f80a40eba40` | No |
| `order_id` | `STRING` | The order being reviewed. Foreign key to `orders`. | `73fc7af87114b39712e6da79b0a377eb` | No |
| `review_score` | `INTEGER` | Customer satisfaction score on a 1–5 star scale (1 = worst, 5 = best). | `4` | No |
| `review_comment_title` | `STRING` | Short review title submitted by the customer in Brazilian Portuguese. Null for the majority of reviews. | `Muito bom!` | Yes |
| `review_comment_message` | `STRING` | Full review text in Brazilian Portuguese. The primary NLP input. Null for ~59% of reviews. | `Produto chegou antes do prazo!` | Yes |
| `review_creation_date` | `TIMESTAMP` | Timestamp when the customer submitted the review. | `2018-01-18 00:00:00` | No |
| `review_answer_timestamp` | `TIMESTAMP` | Timestamp when Olist responded to the review (if applicable). | `2018-01-18 21:46:59` | No |

#### Score Distribution Reference

| Score | Count | Percentage |
|---|---|---|
| 5 ⭐⭐⭐⭐⭐ | 59,600 | 60.1% |
| 4 ⭐⭐⭐⭐ | 19,232 | 19.4% |
| 3 ⭐⭐⭐ | 8,656 | 8.7% |
| 2 ⭐⭐ | 3,168 | 3.2% |
| 1 ⭐ | 8,568 | 8.6% |
| **Bad reviews (≤3)** | **20,392** | **23.0%** |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| 59% null review text | 🟠 High | Only ~41K of 99K reviews contain free text; the rest have score only | NLP pipeline must handle empty/null text gracefully. Do not drop rows — star score is independently valuable. |
| Language: Brazilian Portuguese | 🟠 High | All free-text content is in Portuguese. Standard English NLP tools will fail or produce meaningless results. | Use `spacy[pt_core_news_sm]` for tokenisation. Use BERTimbau (`neuralmind/bert-base-portuguese-cased`) for sentiment classification. |
| Duplicate reviews per order | 🟡 Medium | A small number of `order_id` values appear more than once in this table | Deduplicate in Silver: keep row with the latest `review_creation_date` per `order_id` |
| Average response time | 🟢 Low | Avg 10h 29m between delivery and review submission (median 6h 15m) | Use `hours_to_review` as a derived feature; very fast reviews may indicate unsolicited negative feedback |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw load. Free-text preserved as-is in Portuguese. Partitioned by `review_creation_year`. |
| **Silver** | Deduplicate per `order_id`. Classify `review_sentiment`: `positive` (score ≥ 4), `neutral` (score = 3), `negative` (score ≤ 2). Strip null text. Compute `hours_to_review`. Join to `silver_orders` to add `is_late` flag for correlation. |
| **Gold / dbt** | `fact_reviews` table with sentiment score and delivery performance join. `dim_review_score` for score-based filtering. Aggregated `avg_review_score` joined to `fact_sales` via `order_id`. |
| **Fabric Warehouse** | Hash distributed on `order_id`. Clustered columnstore index. |
| **Power BI** | Customer satisfaction KPI tile. Star score distribution chart. Sentiment trend over time. Bad review rate by category. |
| **Machine Learning** | NLP: BERTimbau fine-tuned for sentiment classification on ~41K Portuguese texts. Topic modelling (LDA) on negative review messages. Churn: `review_score` and `review_sentiment` as strong predictive features (≤ 2 stars → significantly elevated churn probability). |

---

### 📦 Table: `products`

#### Purpose

The product catalogue. Contains physical attributes and category classifications for every product SKU that appears in Olist order history. Enables product performance analysis, category-level aggregations, and feature engineering for demand forecasting.

#### Business Importance

Products are the merchandise layer of the marketplace. While the dataset anonymises product names, the physical attributes (weight, dimensions) allow for freight cost validation, and the category hierarchy enables the most commonly requested business breakdown: revenue and reviews by product category.

#### Granularity

One row represents one unique product SKU. Products are not versioned — price changes and category reclassifications do not create new rows.

#### Primary Key

`product_id`

#### Foreign Keys

- `product_category_name` → `product_category_translation.product_category_name`
- Referenced by: `order_items.product_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `order_items` | `product_id` | 1:N | One product → many order line items |
| `product_category_translation` | `product_category_name` | N:1 | Many products → one category translation |

#### Business Questions Supported

- Which product categories drive the most revenue and order volume?
- Do heavier or larger products incur proportionally higher freight costs?
- Which categories receive the highest and lowest average review scores?
- What is the relationship between product listing quality (photo count, description length) and review score?
- Which product categories are growing vs declining across the 2016–2018 period?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `product_id` | `STRING` | Unique anonymised product identifier. | `1e9e8ef04dbcff4541ed26657ea517e5` | No |
| `product_category_name` | `STRING` | Product category name in Brazilian Portuguese. Must be joined with `product_category_translation` for English display. | `cama_mesa_banho` | Yes |
| `product_name_length` | `INTEGER` | Character count of the product listing title. Used as a proxy for listing quality (product names are anonymised). | `58` | Yes |
| `product_description_length` | `INTEGER` | Character count of the product description text. Higher values suggest more detailed listings. | `1020` | Yes |
| `product_photos_qty` | `INTEGER` | Number of photos in the product listing. Proxy for listing quality. Correlated with conversion and review score. | `4` | Yes |
| `product_weight_g` | `INTEGER` | Product weight in grams. Used to validate freight cost. | `650` | Yes |
| `product_length_cm` | `INTEGER` | Package length in centimetres. | `28` | Yes |
| `product_height_cm` | `INTEGER` | Package height in centimetres. | `9` | Yes |
| `product_width_cm` | `INTEGER` | Package width in centimetres. | `15` | Yes |

#### Derived Columns (Silver Layer)

| Derived Column | Formula | Purpose |
|---|---|---|
| `product_volume_cm3` | `length_cm × height_cm × width_cm` | Volumetric size for freight validation and logistics analysis |
| `category_name_en` | JOIN to `product_category_translation` | English category name for all dashboard and report displays |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| 610 null category names | 🟠 High | 1.9% of products have no category — likely deleted or unlisted categories. These products still appear in order history. | Assign to `'unknown'` category in Silver. Do not drop — these products have real revenue. |
| 3 unmapped Portuguese categories | 🟠 High | `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`, and one unlabelled category have no matching row in `product_category_translation` | Apply manual override mapping in Silver dbt model. Add dbt test: assert 100% category coverage after override. |
| 2 null physical dimension records | 🟢 Low | 2 products with null weight and size columns | Impute with category median values in Silver for freight validation only |
| Product versioning gap | 🟢 Low | Products are not versioned; price changes are invisible in this dataset | Document assumption: all `order_items.price` values are point-in-time actuals; `products` table contains metadata only |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw CSV. All numeric columns loaded as nullable integers. |
| **Silver** | Join with `silver_category_lookup` to add `category_name_en`. Impute null categories as `'unknown'`. Compute `product_volume_cm3`. Apply dimension imputation for 2 null records. |
| **Gold / dbt** | `dim_products` dimension table. Category hierarchy: `category_name_en` as primary grouping attribute. |
| **Fabric Warehouse** | Replicated distribution (32K rows). |
| **Power BI** | Category performance matrix. Revenue by category treemap. Product photo count vs review score scatter. |
| **Machine Learning** | Demand: `category_name_en`, `avg_price` (computed from order_items), `avg_review_score` (from reviews), `product_weight_g` as features. Listing quality: `product_photos_qty` as feature for conversion modelling. |

---

### 🏪 Table: `sellers`

#### Purpose

Profiles each independent merchant operating on the Olist marketplace, including geographic location. Enables seller performance analysis, logistics routing assessment, and identification of high-performing and underperforming merchants.

#### Business Importance

Sellers are the supply side of the marketplace. Their geographic concentration in São Paulo (≈70%) is a structural risk factor for delivery times to northern and northeastern Brazil — directly impacting customer satisfaction scores in those regions.

#### Granularity

One row represents one unique seller on the platform.

#### Primary Key

`seller_id`

#### Foreign Keys

Referenced by: `order_items.seller_id`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `order_items` | `seller_id` | 1:N | One seller → many order line items across all orders |
| `geolocation` | `seller_zip_code_prefix` | N:1 | Many sellers → one ZIP centroid (after dedup) |

#### Business Questions Supported

- Which sellers generate the highest revenue and order volume?
- Are sellers in São Paulo delivering faster than sellers in other states?
- Which sellers have the highest bad review rate?
- What is the geographic distribution of the seller network vs customer demand?
- Which sellers consistently miss their `shipping_limit_date` SLAs?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `seller_id` | `STRING` | Unique anonymised seller identifier. | `3442f8959a84dea7ee197c632cb2df15` | No |
| `seller_zip_code_prefix` | `STRING` | First 5 digits of seller's ZIP code. Used for geolocation enrichment. | `13023` | No |
| `seller_city` | `STRING` | Seller's city name. Inconsistent casing in raw data. | `campinas` | No |
| `seller_state` | `STRING` | Two-letter Brazilian state code. | `SP` | No |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| City name casing | 🟢 Low | Lowercase; some with accented characters stripped. Not analytically critical but creates visual inconsistency in dashboards | Standardise to title case in Silver |
| Geographic concentration | 🟢 Low | ~70% of sellers in São Paulo state — structural dataset characteristic, not a data error | Document as a business insight; use as a feature in delivery time models |
| No seller performance metadata | 🟢 Low | All seller KPIs (revenue, avg review score, avg delivery time) must be computed by joining to `order_items` and `orders` — none are stored natively | Compute in Silver/Gold dbt models; expose as `dim_sellers` attributes |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Raw CSV. |
| **Silver** | City name standardisation (title case). ZIP → lat/lng enrichment from `silver_geolocation`. Derive `seller_region` (North, Northeast, Southeast, South, Centre-West). |
| **Gold / dbt** | `dim_sellers` dimension with computed KPIs: `seller_total_orders`, `seller_total_revenue`, `seller_avg_review_score`, `seller_avg_delivery_days`, `seller_on_time_rate`. |
| **Fabric Warehouse** | Replicated distribution (3K rows — very small). |
| **Power BI** | Seller performance leaderboard. Seller geographic heat map. Seller review score distribution. |
| **Machine Learning** | Delivery prediction: `seller_avg_delivery_days`, `seller_bad_review_rate`, `seller_state` as features. Geographic distance between `seller_zip` and `customer_zip` (Haversine) as delivery time predictor. |

---

### 📍 Table: `geolocation`

#### Purpose

Maps Brazilian ZIP code prefixes (first 5 digits of the 8-digit CEP) to geographic coordinates (latitude, longitude) and named locations. The sole source of spatial data in the platform — used to enrich `customers` and `sellers` with coordinates for geographic analysis and mapping.

#### Business Importance

Geographic analysis reveals the structural supply-demand imbalance on the Olist platform: sellers are concentrated in São Paulo while customers are distributed nationally. This spatial gap is the root cause of the delivery performance differences observed across Brazilian states. Geolocation data also enables Haversine distance computation between seller and customer ZIP centroids — a strong predictor of delivery time.

> **⚠️ Critical Warning:** This table contains **261,831 duplicate rows**. Joining without deduplication first will cause catastrophic fan-out multiplication in every downstream query. **Never join raw geolocation to any other table.**

#### Granularity

One row represents one latitude/longitude coordinate point for one ZIP code prefix. Because Brazilian CEPs cover entire streets (not single buildings), a single ZIP prefix may have many valid coordinate pairs — this is the documented source of duplicates.

#### Primary Key

None in raw form. After deduplication in Silver: `geolocation_zip_code_prefix`

#### Foreign Keys

- `geolocation_zip_code_prefix` ↔ `customers.customer_zip_code_prefix`
- `geolocation_zip_code_prefix` ↔ `sellers.seller_zip_code_prefix`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `customers` | `customer_zip_code_prefix` | 1:N | One ZIP centroid → many customers |
| `sellers` | `seller_zip_code_prefix` | 1:N | One ZIP centroid → many sellers |

#### Business Questions Supported

- Where are Olist customers geographically concentrated?
- What is the geographic coverage and density of the seller network?
- How does seller-to-customer distance correlate with delivery time?
- Which states have the lowest seller coverage relative to customer demand?

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `geolocation_zip_code_prefix` | `STRING` | First 5 digits of a Brazilian ZIP code (CEP prefix). Join key to `customers` and `sellers`. | `01037` | No |
| `geolocation_lat` | `DOUBLE` | Latitude coordinate of this ZIP location. Valid range for Brazil: -34 to +5. | `-23.545621` | No |
| `geolocation_lng` | `DOUBLE` | Longitude coordinate of this ZIP location. Valid range for Brazil: -74 to -28. | `-46.639292` | No |
| `geolocation_city` | `STRING` | City name associated with this ZIP location. Spelling varies across duplicate rows. | `são paulo` | No |
| `geolocation_state` | `STRING` | Two-letter state code associated with this ZIP location. | `SP` | No |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| 261,831 duplicate rows (26.2%) | 🔴 Critical | One ZIP prefix has many coordinate pairs. Joining raw table multiplies rows by ~26% on average. | Deduplicate to first occurrence per `geolocation_zip_code_prefix` in Silver. Add dbt test asserting unique `zip_prefix` after Silver load. |
| Out-of-bounds coordinates | 🟡 Medium | Some lat/lng values fall slightly outside Brazilian territory (border edge cases or data entry errors) | Apply bounding box filter in Silver: lat ∈ [-34, 5], lng ∈ [-74, -28] |
| City name spelling variation | 🟢 Low | The same ZIP prefix may have different city name spellings across duplicate rows | After deduplication, apply title-case standardisation |
| Performance: 1M row table | 🟢 Low | Largest table in the dataset by 10×. Spark broadcast join will fail on raw table | Never broadcast raw geolocation. Always deduplicate first (reduces to 738K), then join via sorted merge join in Spark. |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Full raw load — retain all 1M rows as-is. Partitioned by `geolocation_state` for query performance. |
| **Silver** | **Mandatory deduplication**: keep first row per `geolocation_zip_code_prefix`. Apply coordinate bounding box filter. Standardise city names. Join to `silver_customers` and `silver_sellers` to enrich with lat/lng. |
| **Gold / dbt** | `dim_geography` dimension table. Used as an attribute in `dim_customers` and `dim_sellers`. Haversine distance between seller and customer centroids computed as a dbt macro. |
| **Fabric Warehouse** | Replicated distribution (deduped: 738K rows — manageable). |
| **Power BI** | Customer filled map by state. Seller location scatter map. Geographic sales density heat map. |
| **Machine Learning** | Haversine distance between `seller_zip_lat/lng` and `customer_zip_lat/lng` as the primary geographic delivery time feature. |

---

### 🌐 Table: `product_category_translation`

#### Purpose

A reference lookup table mapping 71 Portuguese product category names to their English equivalents. Required for producing readable English-language dashboards and reports from the Portuguese-native `products.product_category_name` column.

#### Business Importance

Without this table, all category-level analytics would display Portuguese identifiers like `cama_mesa_banho` instead of the human-readable `Bed Bath & Table`. This table is small (71 rows) but has wide downstream impact — it is joined into every product and category analysis.

#### Granularity

One row represents one category name mapping (Portuguese → English).

#### Primary Key

`product_category_name` (Portuguese name)

#### Foreign Keys

Referenced by: `products.product_category_name`

#### Relationships

| Related Table | Join Key | Cardinality | Notes |
|---|---|---|---|
| `products` | `product_category_name` | 1:N | One category → many products. 3 Portuguese categories have no matching row (see Data Quality). |

#### Business Questions Supported

*(Reference table — enables English-language category names in all downstream analytics)*

#### Column Dictionary

| Column | Data Type | Description | Example | Nullable |
|---|---|---|---|---|
| `product_category_name` | `STRING` | Original Brazilian Portuguese product category name as stored in the `products` table. | `cama_mesa_banho` | No |
| `product_category_name_english` | `STRING` | English translation of the category name. Stored with underscores — apply display formatting for dashboards. | `bed_bath_table` | No |

#### Data Quality Considerations

| Issue | Severity | Detail | Handling Strategy |
|---|---|---|---|
| 3 missing Portuguese categories | 🟠 High | `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`, and one unlabelled category in `products` have no match in this table | Apply manual override mapping in the Silver `silver_category_lookup` model. Add dbt test: assert 100% join coverage after override. |
| Display formatting | 🟢 Low | English names use underscores (`bed_bath_table`). Dashboards should display spaces and title case (`Bed Bath & Table`) | Apply `REPLACE(INITCAP(...), '_', ' ')` transformation in `dim_products` dbt model |
| Table completeness | 🟢 Low | 71 rows cover 71 of 74 Portuguese category names in `products` — 3 gap (see above) | Resolved by manual override, not a systemic issue |

#### Downstream Usage

| Layer | Usage |
|---|---|
| **Bronze** | Loaded once as a small static reference table. No partitioning needed. |
| **Silver** | Joined to `silver_products` to add `category_name_en`. Manual override applied for 3 unmapped categories. Display-formatted category name (`category_name_display`) computed here. |
| **Gold / dbt** | Embedded in `dim_products` as the `category_en` and `category_display` attributes. Optionally modelled as a standalone `dim_category` if a category hierarchy is introduced. |
| **Fabric Warehouse** | Replicated (71 rows — trivially small). |
| **Power BI** | Display field in all product and category visuals. Slicer filter on category. Category hierarchy in matrix visuals. |
| **Machine Learning** | Category name encoded as a categorical feature after joining to `order_items`. One-hot encoded or target-encoded depending on model type. |

---

## 4. Relationship Matrix

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        OLIST ENTITY RELATIONSHIP MAP                         │
│                                                                              │
│  customers ──────1:N──────► orders ──────1:N──────► order_items             │
│      │                         │                         │       │           │
│      │                      1:N  1:N               N:1       N:1            │
│      │                         │    │                │         │             │
│      │                   order_  order_           products  sellers          │
│      │                   payments reviews             │         │            │
│      │                                          N:1  │         │  N:1       │
│      │                              product_category_│         │            │
│      │                              translation       │         │            │
│      │                                                │         │            │
│  N:1 │                                                          │            │
│      ▼                                                          ▼            │
│  geolocation ◄───────────────────────────────────────── sellers              │
│  (via zip_code_prefix)                         (via seller_zip_code_prefix)  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Relationship Summary Table

| From Table | To Table | Join Key | Cardinality | Business Meaning |
|---|---|---|---|---|
| `customers` | `orders` | `customer_id` | 1:N | One customer context → one or more orders |
| `orders` | `order_items` | `order_id` | 1:N | One order → 1 to 21 line items |
| `orders` | `order_payments` | `order_id` | 1:N | One order → 1 or more payment methods |
| `orders` | `order_reviews` | `order_id` | 1:1 (≈) | One order → one review (deduplicate first) |
| `order_items` | `products` | `product_id` | N:1 | Many order lines → one product SKU |
| `order_items` | `sellers` | `seller_id` | N:1 | Many order lines → one seller |
| `products` | `product_category_translation` | `product_category_name` | N:1 | Many products → one category translation |
| `customers` | `geolocation` | `customer_zip_code_prefix` | N:1 | Many customers → one deduplicated ZIP centroid |
| `sellers` | `geolocation` | `seller_zip_code_prefix` | N:1 | Many sellers → one deduplicated ZIP centroid |

---

## 5. Data Engineering Notes

### Partitioning Strategy

| Table | Layer | Partition Column(s) | Rationale |
|---|---|---|---|
| `orders` | Bronze / Silver | `year(order_purchase_timestamp)`, `month(order_purchase_timestamp)` | Primary time-series analytics pattern. Enables partition pruning on date-range queries. |
| `order_items` | Bronze / Silver | `year(shipping_limit_date)` | Aligns with order partitioning. Enables seller SLA queries by period. |
| `order_reviews` | Bronze / Silver | `year(review_creation_date)` | Sentiment trend analysis by time window. |
| `geolocation` | Bronze | `geolocation_state` | Reduces scan for regional geographic analyses. |
| `customers` | Silver | `customer_state` | Enables efficient state-level customer analytics. |
| `fact_sales` | Fabric DWH | `order_year`, `order_month` | Balances time-range query pruning with month-level reporting granularity. |

### Incremental Loading Strategy

| Pattern | Tables | Details |
|---|---|---|
| **Full load (one-time)** | `geolocation`, `product_category_translation`, `products`, `sellers` | Reference and dimension tables that change rarely or never. |
| **Append-only incremental** | `orders`, `order_items`, `order_payments`, `order_reviews` | New records only, keyed on `order_id`. Use watermark column for delta detection. |
| **Watermark-based CDC** | `orders` (watermark: `order_purchase_timestamp`), `order_reviews` (watermark: `review_creation_date`) | For production live source connections. Identifies new/updated records since last pipeline run. |
| **SCD Type 2 (future)** | `dim_customers`, `dim_products` | Apply if product pricing or customer location tracking becomes a requirement. Not needed for the current static snapshot dataset. |

> **📌 Note:** The Olist dataset is a historical snapshot. True incremental loading applies to the pipeline design pattern, not the current data load. The pipeline should be designed to support incremental modes when a live order feed is connected in production.

### Data Validation Rules

| Table | Validation Rule | dbt Test | Severity |
|---|---|---|---|
| `customers` | `customer_id` is unique and not null | `unique`, `not_null` | 🔴 Critical |
| `orders` | `order_id` is unique and not null | `unique`, `not_null` | 🔴 Critical |
| `orders` | `order_status` is one of 8 defined values | `accepted_values` | 🔴 Critical |
| `order_payments` | After aggregation, exactly one row per `order_id` | `unique` on aggregated model | 🔴 Critical |
| `order_payments` | `payment_type` is one of 5 defined values | `accepted_values` | 🟠 High |
| `order_items` | `price > 0` for all non-gift records | `expression_is_true` | 🟠 High |
| `products` | All `product_id` in `order_items` exist in `products` | `relationships` | 🟠 High |
| `geolocation` | After Silver dedup: `zip_code_prefix` is unique | `unique` | 🔴 Critical |
| `products` | All `product_category_name` have an English translation | `relationships` + override | 🟠 High |
| `order_reviews` | `review_score` between 1 and 5 | `accepted_values` | 🟠 High |
| `orders` | `order_delivered_customer_date >= order_purchase_timestamp` | `expression_is_true` | 🟡 Medium |

### Recommended Storage Formats

| Layer | Format | Reason |
|---|---|---|
| **Bronze** | Delta Lake (Parquet-based) | ACID transactions, time travel, schema evolution, append-only pattern |
| **Silver** | Delta Lake | Same benefits; enables `MERGE INTO` for deduplication patterns |
| **Gold** | Delta Lake + Fabric Warehouse SQL Tables | Delta for Databricks-served ML features; SQL tables for BI and reporting |
| **Fabric DWH** | Native Fabric Warehouse tables | Columnstore indexing, serverless MPP, direct Power BI DirectQuery support |

### Performance Considerations

| Scenario | Risk | Mitigation |
|---|---|---|
| Joining raw `geolocation` (1M rows) | Fan-out join, memory pressure in Spark | Always deduplicate in Silver first (738K rows). Use sort-merge join, not broadcast join. |
| Joining `order_payments` without aggregation | Revenue inflation by ~4.5% | Aggregate to order level before any join. Enforce via dbt model pre-aggregation. |
| Large Power BI DirectQuery on `fact_sales` | Slow dashboard load times | Use pre-aggregated Gold layer tables. Enable Fabric query caching. |
| PySpark on 100K orders | Spark overhead not warranted by data volume | PySpark is used for scalability demonstration and skill development, not for current data volume necessity. Document this explicitly. |

---

## 6. Business Glossary

| Term | Definition |
|---|---|
| **GMV** (Gross Merchandise Value) | Total value of all orders placed on the platform before deducting returns, discounts, or fees. Computed as `SUM(payment_value)` from `order_payments` at order level. In this dataset: approximately R$ 13.6M across the full period. |
| **AOV** (Average Order Value) | GMV divided by total number of orders. Measures the average spend per transaction. Formula: `SUM(payment_value) / COUNT(DISTINCT order_id)`. Influenced strongly by instalment availability. |
| **LTV** (Customer Lifetime Value) | Total revenue attributed to a single customer (`customer_unique_id`) across all their orders. Currently low due to the 3% repeat purchase rate. LTV = `SUM(payment_value)` grouped by `customer_unique_id`. |
| **Order Status** | The current lifecycle stage of an order. Valid values: `delivered` (97.0%), `shipped`, `canceled` (0.6%), `unavailable`, `invoiced`, `processing`, `created`, `approved`. |
| **Review Score** | Customer satisfaction rating on a 1–5 integer scale. Submitted post-delivery. Platform average: 4.08. Scores ≤ 2 are treated as `negative`; ≥ 4 as `positive`; 3 as `neutral`. |
| **Delivery Delay** | A boolean flag (`is_late`) set to TRUE when `order_delivered_customer_date > order_estimated_delivery_date`. Late deliveries have a 4× higher probability of generating a 1-star review. |
| **Repeat Customer** | A physical customer (`customer_unique_id`) who has placed more than one order. Only 3.0% of customers in this dataset qualify — a primary business problem the platform is built to address. |
| **Payment Installments** | The number of monthly credit card instalments elected by the customer. Ranges from 1 (upfront) to 24 months. 50.1% of credit card orders use instalments. High-instalment orders correlate with higher AOV. |
| **Customer Retention** | The ability of the platform to bring customers back for a second or subsequent purchase. Retention rate = repeat customers / total unique customers. Currently 3.0% — critically low. |
| **Product Category** | A classification grouping of products. Stored in Portuguese in `products.product_category_name`; translated to English via `product_category_translation`. 71 active categories. Top categories by revenue: `health_beauty`, `watches_gifts`, `bed_bath_table`. |
| **RFM** | Recency, Frequency, Monetary — a customer segmentation framework. Recency: days since last order. Frequency: number of orders. Monetary: total spend. Computed from `orders` and `order_payments` grouped by `customer_unique_id`. Primary feature set for the churn prediction model. |
| **Churn** | For this platform, churn is defined as a customer who has not placed a second order within a defined observation window. Given the 3% repeat rate, most customers are effectively churned after their first purchase. Churn label must be engineered, not observed directly. |
| **Freight Ratio** | `freight_value / price` per line item. Measures shipping cost as a proportion of product price. High freight ratios may indicate pricing uncompetitiveness or logistics inefficiency for a product category. |
| **Boleto** | A Brazilian payment method — a bank slip printed by the customer and paid at banks, lottery shops, or online banking. Non-instant; typically clears within 1–3 business days. Represents 19.0% of Olist payment transactions. |
| **CEP** (Código de Endereçamento Postal) | Brazilian postal code system. 8 digits, with the first 5 used as the ZIP prefix in this dataset. One prefix can map to multiple streets, explaining the geolocation duplicate rows. |
| **Demand Forecasting** | Prediction of future order volumes by product category and time period. Uses `order_purchase_timestamp` and `product_category_name` as the primary inputs. Implemented using Prophet or LightGBM with lag features. |
| **Sentiment** | Derived classification of a customer review as `positive` (score ≥ 4), `neutral` (score = 3), or `negative` (score ≤ 2). Used as both a standalone KPI and as a feature in the churn model. |

---

## 7. Final Summary

### Most Important Tables

| Rank | Table | Reason |
|---|---|---|
| 1 | `orders` | Central hub entity. Every analytical workload passes through this table. |
| 2 | `order_items` | Revenue source of truth at product and seller level. |
| 3 | `customers` | Foundation of all customer analytics and ML targets. |
| 4 | `order_reviews` | Sole source of satisfaction data and NLP training material. |
| 5 | `order_payments` | Payment method analytics and order-level revenue aggregation. |

### Largest Tables

| Table | Raw Rows | Post-Silver Rows | Notes |
|---|---|---|---|
| `geolocation` | 1,000,163 | ~738,332 | Only large table; deduplicate before use |
| `order_items` | 112,650 | ~112,650 | Stable post-Silver |
| `order_payments` | 103,886 | ~99,441 (aggregated) | Aggregated to order grain in Silver |
| `orders` | 99,441 | ~99,439 (2 removed) | 2 corrupt records removed |
| `customers` | 99,441 | 99,441 | No row changes |

### Tables Requiring Special Handling

| Table | Special Handling Required |
|---|---|
| `geolocation` | **Mandatory deduplication** in Silver before any join. Largest table by 10×. Never broadcast in Spark. |
| `order_payments` | **Mandatory aggregation** by `order_id` before joining to any order-level table. Raw join inflates revenue by ~4.5%. |
| `orders` | Complex null handling with business logic rules. 2 corrupt records must be removed. 5 derived timestamp columns computed in Silver. |
| `order_reviews` | Portuguese NLP. ~59% null text fields. Duplicate reviews per order must be deduplicated. |
| `products` | 3 unmapped categories require manual Silver override. 610 null category names require `'unknown'` imputation. |

### Tables That Feed ML Models

| Model | Primary Tables |
|---|---|
| **Churn Prediction** | `customers`, `orders`, `order_items`, `order_payments`, `order_reviews` |
| **Demand Forecasting** | `orders`, `order_items`, `products`, `product_category_translation` |
| **NLP Sentiment** | `order_reviews` (primary), `orders` (for delivery context join) |

### Tables That Feed Power BI Dashboards

| Dashboard | Tables via Gold Layer |
|---|---|
| Sales Performance | `fact_sales` ← `orders`, `order_items`, `order_payments` |
| Delivery Performance | `fact_deliveries` ← `orders` |
| Customer Satisfaction | `fact_reviews` ← `order_reviews`, `orders` |
| Category Analytics | `dim_products` ← `products`, `product_category_translation` |
| Geographic Analysis | `dim_geography` ← `geolocation`, `customers`, `sellers` |
| Seller Scorecards | `dim_sellers` ← `sellers`, `order_items`, `orders`, `order_reviews` |

### Tables Critical for Data Warehouse Star Schema

| Warehouse Object | Source Tables | Layer |
|---|---|---|
| `fact_sales` | `order_items`, `orders`, `order_payments` | Gold |
| `fact_deliveries` | `orders` | Gold |
| `fact_reviews` | `order_reviews`, `orders` | Gold |
| `dim_customers` | `customers`, `geolocation` | Gold |
| `dim_products` | `products`, `product_category_translation` | Gold |
| `dim_sellers` | `sellers`, `geolocation` | Gold |
| `dim_date` | Generated date spine | Gold |
| `dim_geography` | `geolocation` | Gold |
| `dim_payment_method` | `order_payments` | Gold |

---

> *Document maintained by the Olist E-Commerce Intelligence Platform Data Engineering Team · v1.0.0 · Last updated July 2025*
>
> *For corrections or additions, open a pull request against the `/docs` directory in the project repository and tag the Data Architecture team for review.*

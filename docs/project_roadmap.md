# Project Roadmap

## Phase 1: Infrastructure Setup

Initialize the repository structure, local development workflow, configuration management, dependency files, Docker placeholders, and team documentation.

## Phase 2: Data Understanding & Profiling

Profile the Olist dataset, document source schemas, identify data quality issues, and define initial business domains.

## Phase 3: Kafka Ingestion

Design and implement local Kafka producers and consumers for source event simulation and ingestion contracts.

## Phase 4: Bronze Layer

Build raw landing pipelines that preserve source fidelity, ingestion metadata, lineage, and replay capability.

## Phase 5: Silver Layer

Implement cleaning, standardization, deduplication, type enforcement, and core data quality validation.

## Phase 6: dbt Models

Create dbt staging, intermediate, and mart models with tests, documentation, and reusable transformation logic.

## Phase 7: Gold Layer

Publish business-ready datasets for sales, customers, products, sellers, orders, payments, logistics, and reviews.

## Phase 8: Fabric Warehouse

Load curated outputs into Microsoft Fabric Warehouse and establish warehouse schemas, access patterns, and governance.

## Phase 9: Machine Learning

Develop machine learning use cases such as demand forecasting, customer segmentation, delivery delay prediction, and review sentiment analysis.

## Phase 10: API Layer

Expose selected data products and model outputs through FastAPI with typed contracts, validation, and observability.

## Phase 11: Dashboard

Build Power BI and Streamlit reporting experiences for business metrics, operational monitoring, and model insights.

## Phase 12: Deployment

Prepare CI/CD, environment promotion, monitoring, alerting, secrets management, and operational runbooks.

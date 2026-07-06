# Ingestion Module

The ingestion module prepares reusable components for future batch and real-time data ingestion workflows. At this phase, it defines contracts, configuration objects, source readers, and starter schemas only. It does not connect to Kafka, send messages, run Spark, or implement pipeline business logic.

## Future Flow

```text
CSV
  |
  v
CSVReader
  |
  v
Producer
  |
  v
Kafka Topic
  |
  v
Spark Consumer
  |
  v
Bronze Layer
```

## Responsibilities

### readers

Reusable source readers live under `readers/`. The initial `CSVReader` provides shared CSV file validation, DataFrame loading, row counting, and preview helpers for future ingestion components.

### producers

Producer classes live under `producers/`. `BaseProducer` defines the producer contract, while domain-specific producers such as `OrdersProducer` and `CustomersProducer` provide explicit extension points for future Kafka implementations.

### schemas

Starter JSON schemas live under `schemas/`. They define the expected shape of future order and customer ingestion records and will later support validation before publishing or landing data.

### utils

Shared configuration and helper code lives under `utils/`. `KafkaConfig` centralizes Kafka-related settings from `configs.settings` without creating Kafka connections.

## Design Notes

- Components are modular so batch and streaming ingestion can evolve independently.
- Producer classes are intentionally stubs until the Kafka implementation phase.
- Shared configuration is loaded from the existing project settings module.
- Business rules and data pipeline orchestration will be added in later phases.

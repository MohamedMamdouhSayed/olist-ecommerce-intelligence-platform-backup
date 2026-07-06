# Testing Strategy

This directory will contain tests that protect the platform as it grows from local scaffolding into a full data product.

## Unit Tests

Unit tests will validate small, deterministic Python functions in isolation. These tests should be fast, run locally, and cover configuration helpers, transformations, utility modules, and API service logic.

## Data Validation Tests

Data validation tests will verify schema expectations, required columns, nullability rules, accepted value ranges, uniqueness constraints, and referential integrity. Great Expectations or equivalent validation tooling will be used where appropriate.

## Integration Tests

Integration tests will validate interactions between components such as ingestion jobs, local infrastructure services, data lake paths, warehouse loaders, and API dependencies. These tests may require Docker services and should be isolated from production resources.

## End-to-End Pipeline Tests

End-to-end tests will exercise representative pipeline runs from source data through curated outputs. These tests should use small sample datasets, validate medallion layer contracts, and provide confidence before deployment.

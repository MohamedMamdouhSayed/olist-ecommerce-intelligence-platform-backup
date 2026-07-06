# Configuration Architecture

The `configs` package centralizes platform configuration for the Olist E-Commerce Intelligence Platform. It is designed for local development today and production Azure deployment later.

## Package Layout

- `config.py`: Pydantic settings model and cached `get_settings()` factory.
- `settings.py`: Backwards-compatible facade for existing imports.
- `environments.py`: Supported environment names: development, testing, and production.
- `constants.py`: Shared constants such as project paths, default log level, and `.env` location.
- `validators.py`: Reusable validation helpers for required strings, paths, and log levels.
- `secrets.py`: Local `.env` secret provider and future Azure Key Vault extension point.
- `logging_config.py`: Central Python logging setup.

## Environment Handling

Configuration values are read from `configs/.env` using Pydantic settings. The supported environments are:

- `development`
- `testing`
- `production`

Set the active environment with:

```text
ENVIRONMENT=development
```

The settings model exposes convenience properties:

- `is_development`
- `is_testing`
- `is_production`

## Validation

The configuration layer validates required values at startup:

- `PROJECT_NAME`
- `DATA_PATH`
- `BRONZE_PATH`
- `SILVER_PATH`
- `GOLD_PATH`
- `KAFKA_BOOTSTRAP_SERVER`
- `KAFKA_TOPIC_ORDERS`
- `SPARK_APP_NAME`

Data paths are resolved relative to the project root and created automatically for local development. Production rules are also enforced, including blocking `LOG_LEVEL=DEBUG` in production.

## Logging

Use `configs.logging_config.configure_logging()` to initialize logging once at application startup. Existing `print` calls should be replaced with module loggers:

```python
from configs.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)
logger.info("Application started")
```

## Azure Key Vault Readiness

The platform remains fully compatible with local `.env` files. Future production deployments can enable Azure Key Vault with:

```text
USE_AZURE_KEY_VAULT=true
AZURE_KEY_VAULT_URL=https://<vault-name>.vault.azure.net/
```

`configs.secrets.AzureKeyVaultSecretProvider` is intentionally a placeholder until the Azure SDK and managed identity strategy are introduced. This keeps local development simple while preserving a clean production extension point.


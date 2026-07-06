"""Secret provider abstractions with local and future Azure Key Vault support."""

import logging
import os
from dataclasses import dataclass
from typing import Protocol


logger = logging.getLogger(__name__)


class SecretProvider(Protocol):
    """Interface for retrieving secrets without coupling callers to a backend."""

    def get_secret(self, name: str) -> str | None:
        """Return a secret value by name if it exists."""


@dataclass(frozen=True)
class LocalEnvSecretProvider:
    """Read secrets from local environment variables.

    This provider keeps local development fully compatible with `.env` files
    loaded by Pydantic settings.
    """

    def get_secret(self, name: str) -> str | None:
        """Read a secret from the process environment."""
        logger.debug("Reading secret '%s' from local environment", name)
        return os.getenv(name)


@dataclass(frozen=True)
class AzureKeyVaultSecretProvider:
    """Placeholder provider for future Azure Key Vault integration.

    The class intentionally avoids importing Azure SDK packages until the
    platform is ready to enable Key Vault. This keeps local development light
    while preserving a clean extension point for production secrets.
    """

    vault_url: str | None

    def get_secret(self, name: str) -> str | None:
        """Return a secret from Azure Key Vault in a future implementation."""
        if not self.vault_url:
            logger.debug("Azure Key Vault URL is not configured; skipping '%s'", name)
            return None

        logger.info("Azure Key Vault lookup requested for '%s'", name)
        raise NotImplementedError(
            "Azure Key Vault integration is reserved for a future platform phase."
        )


def build_secret_provider(
    use_key_vault: bool,
    key_vault_url: str | None,
) -> SecretProvider:
    """Build the appropriate secret provider for the current environment."""
    if use_key_vault:
        return AzureKeyVaultSecretProvider(vault_url=key_vault_url)

    return LocalEnvSecretProvider()


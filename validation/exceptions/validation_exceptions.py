"""Custom exceptions raised by the data validation framework."""


class ValidationError(Exception):
    """Base exception for validation framework errors."""


class SchemaValidationError(ValidationError):
    """Raised when schema validation configuration or execution fails."""


class BusinessRuleError(ValidationError):
    """Raised when a business rule is invalid or cannot be evaluated."""


class ReferentialIntegrityError(ValidationError):
    """Raised when referential integrity validation cannot be evaluated."""


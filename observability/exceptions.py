"""Custom exceptions for the observability framework."""


class ObservabilityError(Exception):
    """Base exception for observability framework errors."""


class LoggerConfigurationError(ObservabilityError):
    """Raised when logger configuration is invalid."""


class MonitoringError(ObservabilityError):
    """Raised when monitoring operations fail."""


class HealthCheckError(ObservabilityError):
    """Raised when health check configuration or execution fails."""


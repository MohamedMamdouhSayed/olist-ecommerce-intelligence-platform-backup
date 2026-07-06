"""Reusable validation result objects."""

from dataclasses import dataclass
from enum import Enum


class ValidationStatus(str, Enum):
    """Supported validation execution statuses."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class ValidationSeverity(str, Enum):
    """Supported validation severities."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ValidationResult:
    """Result emitted by a single validator execution."""

    validation_name: str
    status: ValidationStatus
    severity: ValidationSeverity
    rows_checked: int
    rows_failed: int
    error_count: int
    execution_time_seconds: float
    message: str
    failed_indices: list[int] | None = None

    @property
    def passed(self) -> bool:
        """Return whether the validation passed."""
        return self.status == ValidationStatus.PASSED

    @property
    def failed(self) -> bool:
        """Return whether the validation failed."""
        return self.status == ValidationStatus.FAILED

    @property
    def warning(self) -> bool:
        """Return whether the validation produced a warning."""
        return self.status == ValidationStatus.WARNING

    def to_dict(self) -> dict[str, object]:
        """Return a dictionary representation for reports and tests."""
        return {
            "validation_name": self.validation_name,
            "status": self.status.value,
            "severity": self.severity.value,
            "rows_checked": self.rows_checked,
            "rows_failed": self.rows_failed,
            "error_count": self.error_count,
            "execution_time_seconds": self.execution_time_seconds,
            "message": self.message,
            "failed_indices": self.failed_indices,
        }


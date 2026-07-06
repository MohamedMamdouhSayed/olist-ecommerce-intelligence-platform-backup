"""Abstract validator contract for all validation checks."""

from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any

import pandas as pd

from validation.validation_result import (
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
)


class ValidatorBase(ABC):
    """Base class for independent data validators."""

    def __init__(
        self,
        validation_name: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize a validator with a stable validation name and severity."""
        self.validation_name = validation_name
        self.severity = severity

    @abstractmethod
    def validate(self, dataframe: pd.DataFrame) -> ValidationResult:
        """Validate a DataFrame and return a structured result."""

    def _start_timer(self) -> float:
        """Start a high-resolution execution timer."""
        return perf_counter()

    def _elapsed_seconds(self, start_time: float) -> float:
        """Return elapsed seconds rounded for stable report output."""
        return round(perf_counter() - start_time, 6)

    def _build_result(
        self,
        status: ValidationStatus,
        rows_checked: int,
        rows_failed: int,
        error_count: int,
        execution_time_seconds: float,
        message: str,
        metadata: dict[str, Any] | None = None,
        failed_indices: list[int] | None = None,
    ) -> ValidationResult:
        """Build a standard validation result."""
        if metadata:
            message = f"{message} | metadata={metadata}"

        return ValidationResult(
            validation_name=self.validation_name,
            status=status,
            severity=self.severity,
            rows_checked=rows_checked,
            rows_failed=rows_failed,
            error_count=error_count,
            execution_time_seconds=execution_time_seconds,
            message=message,
            failed_indices=failed_indices,
        )


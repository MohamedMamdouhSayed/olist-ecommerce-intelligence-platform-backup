"""Range validation for numeric and comparable columns."""

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from validation.validation_result import ValidationSeverity, ValidationStatus
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RangeRule:
    """Range rule for a single comparable column."""

    column: str
    min_value: Any | None = None
    max_value: Any | None = None
    inclusive_min: bool = True
    inclusive_max: bool = True


class RangeValidator(ValidatorBase):
    """Validate values against configured range rules."""

    def __init__(
        self,
        rules: list[RangeRule],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize range validation rules."""
        super().__init__("range_validation", severity)
        if not rules:
            raise ValueError("RangeValidator requires at least one RangeRule.")

        self.rules = rules

    def validate(self, dataframe: pd.DataFrame):
        """Validate range rules for configured columns."""
        start_time = self._start_timer()
        logger.debug("Validating %s range rules", len(self.rules))

        missing_columns: list[str] = []
        rule_failures: dict[str, int] = {}
        rows_failed_mask = pd.Series(False, index=dataframe.index)

        for rule in self.rules:
            if rule.column not in dataframe.columns:
                missing_columns.append(rule.column)
                continue

            invalid_mask = pd.Series(False, index=dataframe.index)
            series = dataframe[rule.column]

            if rule.min_value is not None:
                invalid_mask = invalid_mask | (
                    series < rule.min_value if rule.inclusive_min else series <= rule.min_value
                )

            if rule.max_value is not None:
                invalid_mask = invalid_mask | (
                    series > rule.max_value if rule.inclusive_max else series >= rule.max_value
                )

            failure_count = int(invalid_mask.sum())
            if failure_count:
                rule_failures[rule.column] = failure_count
                rows_failed_mask = rows_failed_mask | invalid_mask

        error_count = len(missing_columns) + len(rule_failures)
        status = ValidationStatus.PASSED if error_count == 0 else ValidationStatus.FAILED

        return self._build_result(
            status=status,
            rows_checked=len(dataframe),
            rows_failed=int(rows_failed_mask.sum()),
            error_count=error_count,
            execution_time_seconds=self._elapsed_seconds(start_time),
            message="Range validation passed." if status == ValidationStatus.PASSED else "Range validation failed.",
            metadata={
                "missing_columns": missing_columns,
                "rule_failures": rule_failures,
            },
        )


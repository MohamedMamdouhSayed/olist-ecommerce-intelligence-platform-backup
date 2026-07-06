"""Null validation for required fields and configurable thresholds."""

import logging

import pandas as pd

from validation.validation_result import ValidationSeverity, ValidationStatus
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


class NullValidator(ValidatorBase):
    """Validate null counts and null percentages for required fields."""

    def __init__(
        self,
        required_fields: list[str],
        null_threshold_percent: float = 0.0,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize null validation rules."""
        super().__init__("null_validation", severity)
        if not 0 <= null_threshold_percent <= 100:
            raise ValueError("null_threshold_percent must be between 0 and 100.")

        self.required_fields = required_fields
        self.null_threshold_percent = null_threshold_percent

    def validate(self, dataframe: pd.DataFrame):
        """Validate nulls for configured fields."""
        start_time = self._start_timer()
        logger.debug("Validating nulls for fields: %s", self.required_fields)

        missing_fields = [field for field in self.required_fields if field not in dataframe.columns]
        field_failures: dict[str, dict[str, float | int]] = {}
        rows_failed_mask = pd.Series(False, index=dataframe.index)

        for field in self.required_fields:
            if field not in dataframe.columns:
                continue

            null_mask = dataframe[field].isna()
            null_count = int(null_mask.sum())
            null_percent = round((null_count / len(dataframe)) * 100, 4) if len(dataframe) else 0.0
            if null_percent > self.null_threshold_percent:
                field_failures[field] = {
                    "null_count": null_count,
                    "null_percent": null_percent,
                    "threshold_percent": self.null_threshold_percent,
                }
                rows_failed_mask = rows_failed_mask | null_mask

        error_count = len(missing_fields) + len(field_failures)
        status = ValidationStatus.PASSED if error_count == 0 else ValidationStatus.FAILED

        failed_indices = list(dataframe.index[rows_failed_mask])
        return self._build_result(
            status=status,
            rows_checked=len(dataframe),
            rows_failed=len(failed_indices),
            error_count=error_count,
            execution_time_seconds=self._elapsed_seconds(start_time),
            message="Null validation passed." if status == ValidationStatus.PASSED else "Null validation failed.",
            metadata={
                "missing_fields": missing_fields,
                "field_failures": field_failures,
            },
            failed_indices=failed_indices,
        )


"""Referential integrity validation for tabular datasets."""

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from validation.exceptions.validation_exceptions import ReferentialIntegrityError
from validation.validation_result import ValidationSeverity, ValidationStatus
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReferentialRule:
    """Rule requiring values in a column to exist in a reference set."""

    column: str
    reference_values: Iterable[Any]
    allow_nulls: bool = False
    reference_name: str | None = None


class ReferentialValidator(ValidatorBase):
    """Validate referential integrity against supplied reference values."""

    def __init__(
        self,
        rules: list[ReferentialRule],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize referential integrity validation."""
        super().__init__("referential_integrity_validation", severity)
        if not rules:
            raise ReferentialIntegrityError(
                "ReferentialValidator requires at least one ReferentialRule."
            )

        self.rules = rules

    def validate(self, dataframe: pd.DataFrame):
        """Validate configured referential rules."""
        start_time = self._start_timer()
        logger.debug("Validating %s referential rules", len(self.rules))

        missing_columns: list[str] = []
        rule_failures: dict[str, int] = {}
        rows_failed_mask = pd.Series(False, index=dataframe.index)

        for rule in self.rules:
            if rule.column not in dataframe.columns:
                missing_columns.append(rule.column)
                continue

            reference_values = set(rule.reference_values)
            if not reference_values:
                raise ReferentialIntegrityError(
                    f"Reference values for column '{rule.column}' cannot be empty."
                )

            value_mask = dataframe[rule.column].isin(reference_values)
            if rule.allow_nulls:
                value_mask = value_mask | dataframe[rule.column].isna()

            invalid_mask = ~value_mask
            failure_count = int(invalid_mask.sum())
            if failure_count:
                rule_name = rule.reference_name or rule.column
                rule_failures[rule_name] = failure_count
                rows_failed_mask = rows_failed_mask | invalid_mask

        error_count = len(missing_columns) + len(rule_failures)
        status = ValidationStatus.PASSED if error_count == 0 else ValidationStatus.FAILED

        return self._build_result(
            status=status,
            rows_checked=len(dataframe),
            rows_failed=int(rows_failed_mask.sum()),
            error_count=error_count,
            execution_time_seconds=self._elapsed_seconds(start_time),
            message="Referential integrity validation passed." if status == ValidationStatus.PASSED else "Referential integrity validation failed.",
            metadata={
                "missing_columns": missing_columns,
                "rule_failures": rule_failures,
            },
        )


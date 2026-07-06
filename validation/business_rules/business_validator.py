"""Business-rule validation for domain-specific checks."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from validation.exceptions.validation_exceptions import BusinessRuleError
from validation.validation_result import ValidationSeverity, ValidationStatus
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BusinessRule:
    """Business rule definition.

    The condition callable must return a boolean Series where True means the row
    is valid and False means the row violates the rule.
    """

    name: str
    description: str
    required_columns: list[str]
    condition: Callable[[pd.DataFrame], pd.Series]


class BusinessValidator(ValidatorBase):
    """Validate configurable business rules without hardcoded datasets."""

    def __init__(
        self,
        rules: list[BusinessRule],
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize business-rule validation."""
        super().__init__("business_rule_validation", severity)
        if not rules:
            raise BusinessRuleError("BusinessValidator requires at least one rule.")

        self.rules = rules

    def validate(self, dataframe: pd.DataFrame):
        """Validate all configured business rules."""
        start_time = self._start_timer()
        logger.debug("Validating %s business rules", len(self.rules))

        missing_columns: dict[str, list[str]] = {}
        rule_failures: dict[str, int] = {}
        rows_failed_mask = pd.Series(False, index=dataframe.index)

        for rule in self.rules:
            missing = [
                column for column in rule.required_columns if column not in dataframe.columns
            ]
            if missing:
                missing_columns[rule.name] = missing
                continue

            try:
                valid_mask = rule.condition(dataframe)
            except Exception as exc:
                raise BusinessRuleError(
                    f"Business rule '{rule.name}' could not be evaluated: {exc}"
                ) from exc

            if not isinstance(valid_mask, pd.Series):
                raise BusinessRuleError(
                    f"Business rule '{rule.name}' must return a pandas Series."
                )

            invalid_mask = ~valid_mask.fillna(False)
            failure_count = int(invalid_mask.sum())
            if failure_count:
                rule_failures[rule.name] = failure_count
                rows_failed_mask = rows_failed_mask | invalid_mask

        error_count = len(missing_columns) + len(rule_failures)
        status = ValidationStatus.PASSED if error_count == 0 else ValidationStatus.FAILED

        return self._build_result(
            status=status,
            rows_checked=len(dataframe),
            rows_failed=int(rows_failed_mask.sum()),
            error_count=error_count,
            execution_time_seconds=self._elapsed_seconds(start_time),
            message="Business-rule validation passed." if status == ValidationStatus.PASSED else "Business-rule validation failed.",
            metadata={
                "missing_columns": missing_columns,
                "rule_failures": rule_failures,
            },
        )


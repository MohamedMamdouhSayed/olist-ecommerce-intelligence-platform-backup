"""Duplicate validation for rows and primary keys."""

import logging

import pandas as pd

from validation.validation_result import ValidationSeverity, ValidationStatus
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


class DuplicateValidator(ValidatorBase):
    """Validate duplicate full rows and duplicate primary-key combinations."""

    def __init__(
        self,
        primary_key_columns: list[str] | None = None,
        check_full_row_duplicates: bool = True,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize duplicate validation rules."""
        super().__init__("duplicate_validation", severity)
        self.primary_key_columns = primary_key_columns or []
        self.check_full_row_duplicates = check_full_row_duplicates

    def validate(self, dataframe: pd.DataFrame):
        """Validate duplicate records."""
        start_time = self._start_timer()
        logger.debug("Validating duplicates")

        missing_key_columns = [
            column for column in self.primary_key_columns if column not in dataframe.columns
        ]
        duplicate_row_count = 0
        duplicate_key_count = 0
        rows_failed_mask = pd.Series(False, index=dataframe.index)

        if self.check_full_row_duplicates:
            duplicate_rows = dataframe.duplicated(keep=False)
            duplicate_row_count = int(duplicate_rows.sum())
            rows_failed_mask = rows_failed_mask | duplicate_rows

        if self.primary_key_columns and not missing_key_columns:
            duplicate_keys = dataframe.duplicated(subset=self.primary_key_columns, keep=False)
            duplicate_key_count = int(duplicate_keys.sum())
            rows_failed_mask = rows_failed_mask | duplicate_keys

        error_count = len(missing_key_columns)
        if duplicate_row_count:
            error_count += 1
        if duplicate_key_count:
            error_count += 1

        status = ValidationStatus.PASSED if error_count == 0 else ValidationStatus.FAILED

        return self._build_result(
            status=status,
            rows_checked=len(dataframe),
            rows_failed=int(rows_failed_mask.sum()),
            error_count=error_count,
            execution_time_seconds=self._elapsed_seconds(start_time),
            message="Duplicate validation passed." if status == ValidationStatus.PASSED else "Duplicate validation failed.",
            metadata={
                "missing_key_columns": missing_key_columns,
                "duplicate_row_count": duplicate_row_count,
                "duplicate_key_count": duplicate_key_count,
            },
        )


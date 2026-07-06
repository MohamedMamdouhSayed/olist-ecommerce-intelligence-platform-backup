"""Schema validation for tabular datasets."""

import logging

import pandas as pd

from validation.exceptions.validation_exceptions import SchemaValidationError
from validation.validation_result import ValidationSeverity, ValidationStatus
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


class SchemaValidator(ValidatorBase):
    """Validate required columns, extra columns, and expected data types."""

    def __init__(
        self,
        required_columns: list[str],
        expected_dtypes: dict[str, str] | None = None,
        allow_extra_columns: bool = True,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """Initialize schema validation rules."""
        super().__init__("schema_validation", severity)
        if not required_columns:
            raise SchemaValidationError("SchemaValidator requires at least one column.")

        self.required_columns = required_columns
        self.expected_dtypes = expected_dtypes or {}
        self.allow_extra_columns = allow_extra_columns

    def validate(self, dataframe: pd.DataFrame):
        """Validate the DataFrame schema."""
        start_time = self._start_timer()
        logger.debug("Validating schema for %s columns", len(dataframe.columns))

        actual_columns = set(dataframe.columns)
        required_columns = set(self.required_columns)
        expected_columns = required_columns | set(self.expected_dtypes.keys())

        missing_columns = sorted(required_columns - actual_columns)
        extra_columns = sorted(actual_columns - expected_columns)
        dtype_errors: dict[str, str] = {}
        failed_indices = []

        for column_name, expected_dtype in self.expected_dtypes.items():
            if column_name not in actual_columns:
                continue

            # Identify rows with incorrect dtypes if possible, 
            # though usually dtypes are per-column in pandas.
            # If a column has mixed types, actual_dtype will be 'object'.
            actual_dtype = str(dataframe[column_name].dtype)
            if actual_dtype != expected_dtype:
                dtype_errors[column_name] = (
                    f"expected={expected_dtype}, actual={actual_dtype}"
                )

        error_count = len(missing_columns) + len(dtype_errors)
        if not self.allow_extra_columns:
            error_count += len(extra_columns)

        if missing_columns:
            # If columns are missing, all rows are effectively invalid for this schema
            failed_indices = list(dataframe.index)

        status = ValidationStatus.PASSED if error_count == 0 else ValidationStatus.FAILED
        message = "Schema validation passed."
        if error_count:
            message = "Schema validation failed."

        return self._build_result(
            status=status,
            rows_checked=len(dataframe),
            rows_failed=len(failed_indices),
            error_count=error_count,
            execution_time_seconds=self._elapsed_seconds(start_time),
            message=message,
            metadata={
                "missing_columns": missing_columns,
                "extra_columns": extra_columns,
                "dtype_errors": dtype_errors,
            },
            failed_indices=failed_indices,
        )


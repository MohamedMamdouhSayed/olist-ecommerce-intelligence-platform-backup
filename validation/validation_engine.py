"""Validation engine for orchestrating independent validators."""

import logging
from time import perf_counter

import pandas as pd

from validation.reports.quality_report import QualityReport
from validation.validation_result import (
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
)
from validation.validator_base import ValidatorBase


logger = logging.getLogger(__name__)


class ValidationEngine:
    """Register validators, execute them sequentially, and aggregate results."""

    def __init__(self) -> None:
        """Create an empty validation engine."""
        self._validators: list[ValidatorBase] = []

    def register_validator(self, validator: ValidatorBase) -> None:
        """Register a validator to run during validation execution."""
        logger.debug("Registering validator: %s", validator.validation_name)
        self._validators.append(validator)

    def register_validators(self, validators: list[ValidatorBase]) -> None:
        """Register multiple validators in execution order."""
        for validator in validators:
            self.register_validator(validator)

    def run(self, dataframe: pd.DataFrame) -> QualityReport:
        """Run all validators sequentially and return a quality report."""
        logger.info("Starting validation run with %s validators", len(self._validators))
        start_time = perf_counter()
        results: list[ValidationResult] = []

        for validator in self._validators:
            logger.debug("Running validator: %s", validator.validation_name)
            try:
                results.append(validator.validate(dataframe))
            except Exception as exc:
                logger.exception("Validator failed unexpectedly: %s", validator.validation_name)
                results.append(
                    ValidationResult(
                        validation_name=validator.validation_name,
                        status=ValidationStatus.FAILED,
                        severity=ValidationSeverity.CRITICAL,
                        rows_checked=len(dataframe),
                        rows_failed=len(dataframe),
                        error_count=1,
                        execution_time_seconds=0.0,
                        message=f"Unexpected validation error: {exc}",
                    )
                )

        execution_time_seconds = round(perf_counter() - start_time, 6)
        report = QualityReport.from_results(
            results=results,
            execution_time_seconds=execution_time_seconds,
        )
        logger.info(
            "Validation run completed: score=%s, checks=%s",
            report.overall_quality_score,
            report.total_checks,
        )
        return report

    def summary(self, report: QualityReport) -> dict[str, object]:
        """Return a compact validation summary for callers."""
        return report.to_dict()["validation_summary"]


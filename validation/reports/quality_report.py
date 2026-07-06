"""Structured data quality reports produced by validation runs."""

from dataclasses import dataclass

from validation.validation_result import ValidationResult


@dataclass(frozen=True)
class QualityReport:
    """Aggregated quality report for a validation execution."""

    total_checks: int
    passed_checks: list[ValidationResult]
    failed_checks: list[ValidationResult]
    warnings: list[ValidationResult]
    execution_time_seconds: float
    overall_quality_score: float

    @classmethod
    def from_results(
        cls,
        results: list[ValidationResult],
        execution_time_seconds: float,
    ) -> "QualityReport":
        """Build a report from individual validation results."""
        total_checks = len(results)
        passed_checks = [result for result in results if result.passed]
        failed_checks = [result for result in results if result.failed]
        warnings = [result for result in results if result.warning]

        if total_checks == 0:
            quality_score = 100.0
        else:
            quality_score = round((len(passed_checks) / total_checks) * 100, 2)

        return cls(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warnings=warnings,
            execution_time_seconds=execution_time_seconds,
            overall_quality_score=quality_score,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a serializable representation of the quality report."""
        return {
            "validation_summary": {
                "total_checks": self.total_checks,
                "passed_checks": len(self.passed_checks),
                "failed_checks": len(self.failed_checks),
                "warnings": len(self.warnings),
                "overall_quality_score": self.overall_quality_score,
            },
            "passed_checks": [result.to_dict() for result in self.passed_checks],
            "failed_checks": [result.to_dict() for result in self.failed_checks],
            "warnings": [result.to_dict() for result in self.warnings],
            "execution_statistics": {
                "execution_time_seconds": self.execution_time_seconds,
                "validator_execution_time_seconds": round(
                    sum(
                        result.execution_time_seconds
                        for result in (
                            self.passed_checks + self.failed_checks + self.warnings
                        )
                    ),
                    6,
                ),
            },
        }


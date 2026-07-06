"""Generic health checks for platform components."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from observability.exceptions import HealthCheckError


class HealthStatus(str, Enum):
    """Supported health check statuses."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"


@dataclass(frozen=True)
class HealthCheckResult:
    """Result returned by a health check."""

    component_name: str
    status: HealthStatus
    message: str

    def to_dict(self) -> dict[str, str]:
        """Return a serializable health check result."""
        return {
            "component_name": self.component_name,
            "status": self.status.value,
            "message": self.message,
        }


class HealthChecker:
    """Register and run generic health checks."""

    def __init__(self) -> None:
        """Create an empty health checker."""
        self._checks: dict[str, Callable[[], HealthCheckResult]] = {}

    def register_check(
        self,
        component_name: str,
        check: Callable[[], HealthCheckResult],
    ) -> None:
        """Register a named health check."""
        if not component_name.strip():
            raise HealthCheckError("component_name cannot be empty.")

        self._checks[component_name] = check

    def check_configuration(self, required_values: dict[str, object]) -> HealthCheckResult:
        """Check that required configuration values are present."""
        missing_values = [
            name for name, value in required_values.items() if value is None or value == ""
        ]

        if missing_values:
            return HealthCheckResult(
                component_name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing configuration values: {missing_values}",
            )

        return HealthCheckResult(
            component_name="configuration",
            status=HealthStatus.HEALTHY,
            message="Required configuration values are present.",
        )

    def check_file_system_path(
        self,
        component_name: str,
        path: str | Path,
        must_exist: bool = True,
    ) -> HealthCheckResult:
        """Check that a file system path is available."""
        resolved_path = Path(path).expanduser()
        exists = resolved_path.exists()

        if must_exist and not exists:
            return HealthCheckResult(
                component_name=component_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Path does not exist: {resolved_path}",
            )

        return HealthCheckResult(
            component_name=component_name,
            status=HealthStatus.HEALTHY,
            message=f"Path is available: {resolved_path}",
        )

    def run_all(self) -> list[HealthCheckResult]:
        """Run all registered health checks."""
        results: list[HealthCheckResult] = []
        for component_name, check in self._checks.items():
            try:
                results.append(check())
            except Exception as exc:
                results.append(
                    HealthCheckResult(
                        component_name=component_name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {exc}",
                    )
                )

        return results

    def summary(self) -> dict[str, object]:
        """Return a compact health summary."""
        results = self.run_all()
        return {
            "total_checks": len(results),
            "healthy": sum(1 for result in results if result.status == HealthStatus.HEALTHY),
            "warnings": sum(1 for result in results if result.status == HealthStatus.WARNING),
            "unhealthy": sum(1 for result in results if result.status == HealthStatus.UNHEALTHY),
            "results": [result.to_dict() for result in results],
        }


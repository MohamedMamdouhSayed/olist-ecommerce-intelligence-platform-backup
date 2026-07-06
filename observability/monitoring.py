"""Monitoring service for component execution metrics."""

import logging
from typing import Any

from observability.exceptions import MonitoringError
from observability.metrics import ExecutionMetrics


logger = logging.getLogger(__name__)


class MonitoringService:
    """Register components, record executions, and export metrics."""

    def __init__(self) -> None:
        """Create an empty monitoring service."""
        self._metrics: dict[str, ExecutionMetrics] = {}

    def is_registered(self, component_name: str) -> bool:
        """Check if a component is already registered."""
        return component_name in self._metrics

    def register_component(
        self,
        name: str,
        component_type: str = "generic",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a component for metric tracking."""
        if not name.strip():
            raise MonitoringError("component name cannot be empty.")

        if name not in self._metrics:
            logger.debug("Registering monitored component: %s", name)
            self._metrics[name] = ExecutionMetrics(
                component_name=name
            )

    def record_success(
        self, component_name: str, execution_id: str, duration_ms: float
    ) -> None:
        """Record a successful component execution."""
        self.register_component(component_name)
        self._metrics[component_name].record_success(duration_ms)

    def record_execution(self, component_name: str, duration_ms: float) -> None:
        """Record a successful component execution."""
        self.register_component(component_name)
        self._metrics[component_name].record_success(duration_ms)

    def record_failure(
        self,
        component_name: str,
        execution_id: str,
        duration_ms: float,
        error: Exception | None = None,
    ) -> None:
        """Record a failed component execution."""
        self.register_component(component_name)
        self._metrics[component_name].record_failure(duration_ms)

    def get_metrics(self, component_name: str) -> ExecutionMetrics:
        """Return metrics for a registered component."""
        if component_name not in self._metrics:
            raise MonitoringError(f"Component is not registered: {component_name}")

        return self._metrics[component_name]

    def export_metrics(self) -> dict[str, dict[str, object]]:
        """Export all component metrics as dictionaries."""
        return {
            component_name: metrics.to_dict()
            for component_name, metrics in self._metrics.items()
        }


default_monitoring_service = MonitoringService()


def get_global_monitoring_service() -> MonitoringService:
    """Return the global monitoring service singleton."""
    return default_monitoring_service


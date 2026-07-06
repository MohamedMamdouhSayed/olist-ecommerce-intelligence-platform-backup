"""Reusable execution metrics objects."""

from dataclasses import dataclass, field


@dataclass
class ExecutionMetrics:
    """Track execution counts and duration statistics."""

    component_name: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    durations_ms: list[float] = field(default_factory=list)

    def record_success(self, duration_ms: float) -> None:
        """Record a successful execution."""
        self.execution_count += 1
        self.success_count += 1
        self.durations_ms.append(duration_ms)

    def record_failure(self, duration_ms: float) -> None:
        """Record a failed execution."""
        self.execution_count += 1
        self.failure_count += 1
        self.durations_ms.append(duration_ms)

    @property
    def average_duration_ms(self) -> float:
        """Return average execution duration in milliseconds."""
        if not self.durations_ms:
            return 0.0
        return round(sum(self.durations_ms) / len(self.durations_ms), 3)

    @property
    def maximum_duration_ms(self) -> float:
        """Return maximum execution duration in milliseconds."""
        return round(max(self.durations_ms), 3) if self.durations_ms else 0.0

    @property
    def minimum_duration_ms(self) -> float:
        """Return minimum execution duration in milliseconds."""
        return round(min(self.durations_ms), 3) if self.durations_ms else 0.0

    def to_dict(self) -> dict[str, object]:
        """Return a serializable metrics snapshot."""
        return {
            "component_name": self.component_name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_duration_ms": self.average_duration_ms,
            "maximum_duration_ms": self.maximum_duration_ms,
            "minimum_duration_ms": self.minimum_duration_ms,
        }


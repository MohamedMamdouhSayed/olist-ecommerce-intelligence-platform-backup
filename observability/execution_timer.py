"""Execution timing utilities for functions, pipelines, and validations."""

from contextlib import AbstractContextManager
from dataclasses import dataclass
from time import perf_counter
from types import TracebackType


@dataclass(frozen=True)
class TimerResult:
    """Measured execution timing result."""

    name: str
    duration_seconds: float

    @property
    def duration_ms(self) -> float:
        """Return elapsed duration in milliseconds."""
        return round(self.duration_seconds * 1000, 3)


class ExecutionTimer(AbstractContextManager["ExecutionTimer"]):
    """Context manager for measuring execution duration."""

    def __init__(self, name: str) -> None:
        """Create a timer for a named operation."""
        self.name = name
        self._start_time: float | None = None
        self.result: TimerResult | None = None

    def __enter__(self) -> "ExecutionTimer":
        """Start the timer."""
        self._start_time = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the timer and store the result."""
        self.stop()

    def stop(self) -> TimerResult:
        """Stop the timer and return the timing result."""
        if self._start_time is None:
            raise RuntimeError("ExecutionTimer.stop() called before start.")

        duration_seconds = round(perf_counter() - self._start_time, 6)
        self.result = TimerResult(name=self.name, duration_seconds=duration_seconds)
        return self.result


def measure_execution(function_name: str) -> TimerResult:
    """Create a zero-duration result placeholder for future integrations."""
    return TimerResult(name=function_name, duration_seconds=0.0)


"""Reusable observability decorators."""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar, cast

from observability.execution_timer import ExecutionTimer
from observability.monitoring import MonitoringService, default_monitoring_service


F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


def log_execution(
    execution_id: str | None = None,
    pipeline_stage: str | None = None,
    log: logging.Logger | None = None,
) -> Callable[[F], F]:
    """Log function start, success, failure, and duration."""
    active_logger = log or logger

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with ExecutionTimer(func.__qualname__) as timer:
                active_logger.info(
                    "Execution started",
                    extra={
                        "execution_id": execution_id,
                        "pipeline_stage": pipeline_stage,
                        "duration_ms": None,
                    },
                )
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    timer_result = timer.stop()
                    active_logger.exception(
                        "Execution failed",
                        extra={
                            "execution_id": execution_id,
                            "pipeline_stage": pipeline_stage,
                            "duration_ms": timer_result.duration_ms,
                        },
                    )
                    raise

            duration_ms = timer.result.duration_ms if timer.result else None
            active_logger.info(
                "Execution completed",
                extra={
                    "execution_id": execution_id,
                    "pipeline_stage": pipeline_stage,
                    "duration_ms": duration_ms,
                },
            )
            return result

        return cast(F, wrapper)

    return decorator


def measure_time(log: logging.Logger | None = None) -> Callable[[F], F]:
    """Measure and log function execution duration."""
    active_logger = log or logger

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with ExecutionTimer(func.__qualname__) as timer:
                result = func(*args, **kwargs)

            duration_ms = timer.result.duration_ms if timer.result else None
            active_logger.info(
                "Execution time measured",
                extra={"duration_ms": duration_ms},
            )
            return result

        return cast(F, wrapper)

    return decorator


def track_metrics(
    component_name: str | None = None,
    monitoring_service: MonitoringService = default_monitoring_service,
) -> Callable[[F], F]:
    """Track success, failure, and duration metrics for a function."""

    def decorator(func: F) -> F:
        metric_name = component_name or func.__qualname__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with ExecutionTimer(metric_name) as timer:
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    timer_result = timer.stop()
                    monitoring_service.record_failure(metric_name, timer_result.duration_ms)
                    raise

            if timer.result:
                monitoring_service.record_execution(metric_name, timer.result.duration_ms)
            return result

        return cast(F, wrapper)

    return decorator


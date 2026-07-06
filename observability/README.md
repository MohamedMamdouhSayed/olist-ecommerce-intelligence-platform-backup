# Enterprise Observability Framework

The `observability` package provides reusable observability primitives for the Olist E-Commerce Intelligence Platform. It is framework-only: it does not monitor Kafka, Spark, Synapse, FastAPI, or any business pipeline directly.

## Architecture

```text
Application Module
  |
  +--> Logger / Structured Logs
  +--> ExecutionTimer
  +--> Decorators
  +--> MonitoringService
  +--> HealthChecker
  |
  v
Future Exporters
  |
  +--> Azure Monitor
  +--> Application Insights
  +--> Prometheus
  +--> Grafana
```

## Logging Flow

Use `Logger` or `get_logger()` to create structured JSON logs with standard fields:

- `timestamp`
- `level`
- `module`
- `function`
- `execution_id`
- `pipeline_stage`
- `message`
- `duration_ms`

The logger supports:

- Python logging only
- Console handler
- Rotating file handler
- Configurable log levels
- Structured records for future log analytics

Example:

```python
from pathlib import Path

from observability.logger import get_logger

logger = get_logger(
    name=__name__,
    log_level="INFO",
    log_file=Path("logs/platform.log"),
    enable_file=True,
)

logger.info(
    "Pipeline stage completed",
    extra={
        "execution_id": "run-001",
        "pipeline_stage": "validation",
        "duration_ms": 125.4,
    },
)
```

## Monitoring Flow

`MonitoringService` tracks execution metrics per component:

- Execution count
- Success count
- Failure count
- Average duration
- Maximum duration
- Minimum duration

Example:

```python
from observability.monitoring import MonitoringService

monitor = MonitoringService()
monitor.register_component("silver_validation")
monitor.record_execution("silver_validation", duration_ms=240.5)
metrics = monitor.export_metrics()
```

## Metrics

`ExecutionMetrics` is a lightweight in-memory metrics object. It is intentionally backend-neutral so exporters can later map the same public API to Azure Monitor, Application Insights, Prometheus, or Grafana.

## Decorators

The package exposes reusable decorators:

- `@log_execution`
- `@measure_time`
- `@track_metrics`

Example:

```python
from observability.decorators import log_execution, measure_time, track_metrics

@log_execution(execution_id="run-001", pipeline_stage="validation")
@measure_time()
@track_metrics(component_name="validation_step")
def run_validation() -> None:
    return None
```

## Health Checks

`HealthChecker` currently supports:

- Configuration checks
- File system path checks

Future health checks can be added for:

- Kafka
- Spark
- Synapse
- FastAPI

Example:

```python
from observability.health import HealthChecker

checker = HealthChecker()
result = checker.check_configuration(
    {
        "PROJECT_NAME": "olist-platform",
        "ENVIRONMENT": "development",
    }
)
summary = result.to_dict()
```

## Future Integrations

The public API is intentionally stable and backend-neutral. Future integrations should add exporter adapters rather than changing existing callers:

- Azure Monitor exporter
- Application Insights telemetry client
- Prometheus metrics endpoint
- Grafana dashboards
- Centralized alerting service

## Best Practices

- Use structured logs for every module boundary.
- Track duration around pipeline stages, validations, and future Spark jobs.
- Keep component names stable so metrics can be trended over time.
- Use `MonitoringService` in orchestration code, not inside business rules.
- Treat health checks as startup and readiness checks, not as pipeline logic.
- Do not hardcode project paths inside observability components.


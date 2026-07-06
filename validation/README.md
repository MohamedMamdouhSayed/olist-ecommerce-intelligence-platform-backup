# Enterprise Data Validation Framework

The `validation` package provides a reusable data-quality framework for future Bronze, Silver, Gold, dbt, warehouse, API, and machine-learning workflows. It is intentionally independent: it does not connect to Kafka, use Spark, read CSV files, or execute pipeline logic.

## Purpose

The framework gives every future pipeline stage a consistent way to define, run, and report data-quality checks. Validators are modular and testable, so teams can add dataset-specific rules without changing the core engine.

## Architecture

```text
DataFrame-like input
  |
  v
ValidationEngine
  |
  +--> SchemaValidator
  +--> NullValidator
  +--> DuplicateValidator
  +--> RangeValidator
  +--> BusinessValidator
  +--> ReferentialValidator
  |
  v
ValidationResult[]
  |
  v
QualityReport
```

## Package Layout

- `validation_engine.py`: Registers validators, runs them sequentially, aggregates results, and reports execution time.
- `validator_base.py`: Abstract base class for validators.
- `validation_result.py`: Standard result objects with status, severity, row counts, error counts, and execution time.
- `schema/schema_validator.py`: Required column, missing column, extra column, and data-type checks.
- `nulls/null_validator.py`: Required-field null checks with configurable thresholds.
- `duplicates/duplicate_validator.py`: Duplicate row and duplicate primary-key checks.
- `ranges/range_validator.py`: Numeric and comparable range checks.
- `business_rules/business_validator.py`: Custom business-rule checks.
- `referential/referential_validator.py`: Referential integrity checks against supplied reference values.
- `reports/quality_report.py`: Structured quality reports and quality score.
- `exceptions/validation_exceptions.py`: Custom validation exceptions.

## Validation Flow

1. Pipeline code creates validators with stage-specific rules.
2. Validators are registered in `ValidationEngine`.
3. The engine runs validators sequentially.
4. Each validator returns a `ValidationResult`.
5. The engine aggregates results into a `QualityReport`.
6. Pipeline code decides whether to continue, quarantine records, or fail the stage.

## Example

```python
import pandas as pd

from validation.validation_engine import ValidationEngine
from validation.schema.schema_validator import SchemaValidator
from validation.nulls.null_validator import NullValidator
from validation.duplicates.duplicate_validator import DuplicateValidator
from validation.ranges.range_validator import RangeRule, RangeValidator

dataframe = pd.DataFrame(
    [
        {"order_id": "1", "price": 10.0, "review_score": 5},
        {"order_id": "2", "price": 0.0, "review_score": 4},
    ]
)

engine = ValidationEngine()
engine.register_validators(
    [
        SchemaValidator(required_columns=["order_id", "price", "review_score"]),
        NullValidator(required_fields=["order_id"], null_threshold_percent=0),
        DuplicateValidator(primary_key_columns=["order_id"]),
        RangeValidator(
            rules=[
                RangeRule(column="price", min_value=0),
                RangeRule(column="review_score", min_value=1, max_value=5),
            ]
        ),
    ]
)

report = engine.run(dataframe)
summary = report.to_dict()
```

## Business Rule Examples

```python
from validation.business_rules.business_validator import BusinessRule, BusinessValidator

rules = [
    BusinessRule(
        name="delivery_date_after_purchase_date",
        description="Delivery date must be greater than or equal to purchase date.",
        required_columns=["delivery_date", "purchase_date"],
        condition=lambda df: df["delivery_date"] >= df["purchase_date"],
    ),
    BusinessRule(
        name="payment_installments_positive",
        description="Payment installments must be at least 1.",
        required_columns=["payment_installments"],
        condition=lambda df: df["payment_installments"] >= 1,
    ),
]

validator = BusinessValidator(rules=rules)
```

## Future Bronze and Silver Integration

Future Bronze and Silver pipelines can consume this framework after creating stage DataFrames:

- Bronze can validate source schema, required identifiers, duplicate raw records, and source completeness.
- Silver can validate conformed schemas, business rules, referential integrity, ranges, and curated primary keys.
- Gold and warehouse jobs can validate analytical grains, dimension references, and metric ranges.

The framework should be called by orchestration or transformation code. It should not own ingestion, Spark sessions, file reading, Kafka connections, or persistence decisions.

## Best Practices

- Keep validators small and focused on one responsibility.
- Define dataset-specific rules outside the core framework.
- Treat warning-level checks separately from critical blocking checks.
- Persist `QualityReport.to_dict()` output in future observability layers.
- Unit-test validators with small in-memory DataFrames.
- Use stable validation names so reports can be trended over time.


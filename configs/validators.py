"""Reusable validators for platform configuration values."""

from pathlib import Path

from configs.constants import PROJECT_ROOT


def validate_required_string(value: str, field_name: str) -> str:
    """Validate that a required string setting is present and non-empty."""
    if value is None or not str(value).strip():
        raise ValueError(f"Configuration value '{field_name}' is required.")

    return str(value).strip()


def resolve_project_path(value: str | Path) -> Path:
    """Resolve absolute and project-relative paths consistently."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()

    return (PROJECT_ROOT / path).resolve()


def ensure_directory(path: str | Path) -> Path:
    """Create and validate a directory path used by local development."""
    resolved_path = resolve_project_path(path)
    resolved_path.mkdir(parents=True, exist_ok=True)

    if not resolved_path.is_dir():
        raise NotADirectoryError(f"Configured path is not a directory: {resolved_path}")

    return resolved_path


def validate_log_level(value: str) -> str:
    """Validate and normalize a Python logging level name."""
    allowed_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
    normalized = validate_required_string(value, "LOG_LEVEL").upper()

    if normalized not in allowed_levels:
        raise ValueError(
            f"Invalid LOG_LEVEL '{value}'. Expected one of: {sorted(allowed_levels)}"
        )

    return normalized


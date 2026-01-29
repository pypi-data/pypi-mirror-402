"""Configuration management for iFlow CLI."""

import json
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

# Environment presets - service URLs for each environment
# All environments share the same Zitadel OAuth app (iflow)
ZITADEL_CLIENT_ID = "352780574336811032"  # Single OAuth app for all environments

ENVIRONMENTS = {
    "prod": {
        "name": "Production",
        "domain": "iflow.intelliseq.com",
        "file_url": "https://files.iflow.intelliseq.com",
        "compute_url": "https://compute.iflow.intelliseq.com",
        "admin_url": "https://admin.iflow.intelliseq.com",
        "miner_url": "https://miner.iflow.intelliseq.com",
        "zitadel_issuer": "https://zitadel.iflow.intelliseq.com",
        "zitadel_client_id": ZITADEL_CLIENT_ID,
    },
    "stg": {
        "name": "Staging",
        "domain": "stg.iflow.intelliseq.com",
        "file_url": "https://files.stg.iflow.intelliseq.com",
        "compute_url": "https://compute.stg.iflow.intelliseq.com",
        "admin_url": "https://admin.stg.iflow.intelliseq.com",
        "miner_url": "https://miner.stg.iflow.intelliseq.com",
        "zitadel_issuer": "https://zitadel.iflow.intelliseq.com",
        "zitadel_client_id": ZITADEL_CLIENT_ID,
    },
    "dev": {
        "name": "Development (local)",
        "domain": "flow.labpgx.com",
        "file_url": "https://files.flow.labpgx.com",
        "compute_url": "https://compute.flow.labpgx.com",
        "admin_url": "https://admin.flow.labpgx.com",
        "miner_url": "https://miner.flow.labpgx.com",
        "zitadel_issuer": "https://zitadel.iflow.intelliseq.com",
        "zitadel_client_id": ZITADEL_CLIENT_ID,
    },
}


class FlowConfig(BaseSettings):
    """CLI configuration with defaults."""

    # Current environment
    environment: str = "dev"

    # Default project context (saved after selection)
    project_id: str | None = None
    project_name: str | None = None
    org_id: str | None = None
    org_name: str | None = None
    bucket_name: str | None = None

    # API endpoints (can override per-service)
    file_url: str = "https://files.flow.labpgx.com"
    compute_url: str = "https://compute.flow.labpgx.com"
    admin_url: str = "https://admin.flow.labpgx.com"
    miner_url: str = "https://miner.flow.labpgx.com"

    # Legacy alias for backwards compatibility
    api_url: str = "https://files.flow.labpgx.com"

    # Zitadel OAuth settings
    zitadel_issuer: str = "https://zitadel.iflow.intelliseq.com"
    zitadel_client_id: str = "352780574336811032"

    # Token storage
    keyring_service: str = "iflow"

    model_config = {
        "env_prefix": "FLOW_",
        "env_file": ".env",
        "extra": "ignore",
    }


def get_config_path() -> Path:
    """Get path to config file."""
    config_dir = Path.home() / ".config" / "iflow"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict[str, Any]:
    """Load config from file."""
    config_path = get_config_path()
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save config to file."""
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2))


def get_settings() -> FlowConfig:
    """Get settings with file overrides."""
    file_config = load_config()

    # Create settings, allowing file config to override defaults
    return FlowConfig(**file_config)


def get_default_project() -> str | None:
    """Get default project ID from config."""
    return get_settings().project_id


def set_project_context(
    project_id: str,
    project_name: str,
    org_id: str | None = None,
    org_name: str | None = None,
    bucket_name: str | None = None,
) -> None:
    """Save project context to config."""
    config = load_config()
    config["project_id"] = project_id
    config["project_name"] = project_name
    if org_id:
        config["org_id"] = org_id
    if org_name:
        config["org_name"] = org_name
    if bucket_name:
        config["bucket_name"] = bucket_name
    save_config(config)


def clear_project_context() -> None:
    """Clear saved project context."""
    config = load_config()
    config.pop("project_id", None)
    config.pop("project_name", None)
    config.pop("org_id", None)
    config.pop("org_name", None)
    config.pop("bucket_name", None)
    save_config(config)


def apply_environment(env_key: str) -> None:
    """Apply environment settings to config."""
    if env_key not in ENVIRONMENTS:
        return

    env_preset = ENVIRONMENTS[env_key]
    config = load_config()
    config["environment"] = env_key
    config["file_url"] = env_preset["file_url"]
    config["compute_url"] = env_preset["compute_url"]
    config["admin_url"] = env_preset["admin_url"]
    config["miner_url"] = env_preset["miner_url"]
    config["api_url"] = env_preset["file_url"]
    config["zitadel_issuer"] = env_preset["zitadel_issuer"]
    config["zitadel_client_id"] = env_preset["zitadel_client_id"]

    # Clear project context when switching environments
    config.pop("project_id", None)
    config.pop("project_name", None)
    config.pop("org_id", None)
    config.pop("org_name", None)
    config.pop("bucket_name", None)

    save_config(config)


def get_bucket_name() -> str | None:
    """Get bucket name from config."""
    return get_settings().bucket_name


def normalize_bucket_name(bucket: str | None) -> str | None:
    """Normalize bucket name by removing gs:// or s3:// prefix if present.

    Handles cases where bucket_name might be stored with or without prefix.
    Returns just the bucket name without any prefix.
    """
    if not bucket:
        return None
    if bucket.startswith("gs://"):
        bucket = bucket[5:]
    elif bucket.startswith("s3://"):
        bucket = bucket[5:]
    return bucket.rstrip("/")


def resolve_gcs_path(path: str) -> str:
    """Resolve a path to full GCS URI.

    If path starts with gs://, return as-is.
    Otherwise, prepend the project's bucket.
    """
    if path.startswith("gs://") or path.startswith("s3://"):
        return path

    bucket = normalize_bucket_name(get_bucket_name())
    if not bucket:
        # No bucket configured, return path as-is (will likely fail at API level)
        return path

    # Remove leading slash if present
    path = path.lstrip("/")
    return f"gs://{bucket}/{path}"


def to_relative_path(path: str | None) -> str | None:
    """Convert a full GCS/S3 path to a path relative to project bucket.

    Strips gs://bucket/ or s3://bucket/ prefix, returning just the path.
    Used for user-facing display where bucket context is implicit.

    Examples:
        gs://my-bucket/results/file.vcf -> results/file.vcf
        s3://bucket/data/sample.fastq -> data/sample.fastq
        results/file.vcf -> results/file.vcf (already relative)
    """
    if not path:
        return None
    if path.startswith("gs://"):
        # Format: gs://bucket/path/to/file
        parts = path[5:].split("/", 1)
        return parts[1] if len(parts) > 1 else ""
    if path.startswith("s3://"):
        # Format: s3://bucket/path/to/file
        parts = path[5:].split("/", 1)
        return parts[1] if len(parts) > 1 else ""
    return path  # Already relative


def require_project(project_option: str | None) -> str:
    """Get project ID from option or config, raise if not available."""
    if project_option:
        return project_option

    default_project = get_default_project()
    if default_project:
        return default_project

    raise click.ClickException(
        "No project specified. Either:\n"
        "  - Use -p/--project PROJECT_ID\n"
        "  - Set default with: iflow config select-project"
    )


# Import click here to avoid circular import at module load
import click

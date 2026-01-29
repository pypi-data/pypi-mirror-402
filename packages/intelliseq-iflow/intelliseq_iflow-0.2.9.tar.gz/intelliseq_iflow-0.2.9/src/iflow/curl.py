"""Curl command generator for API calls."""

import json
import shlex
from typing import Any

from iflow.auth import get_stored_token
from iflow.config import get_settings


def generate_curl(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> str:
    """Generate a curl command for an API call.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        url: Full URL for the request
        headers: Optional headers dict
        data: Optional JSON body
        params: Optional query parameters

    Returns:
        Complete curl command string
    """
    parts = ["curl -s"]

    # Method
    if method != "GET":
        parts.append(f"-X {method}")

    # Add query params to URL
    if params:
        param_str = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if param_str:
            url = f"{url}?{param_str}"

    # Headers
    all_headers = headers or {}

    # Add auth header (use stored token directly for curl output)
    token_info = get_stored_token()
    if token_info:
        all_headers["Authorization"] = f"Bearer {token_info.access_token}"

    # Add content-type for POST/PUT
    if data and method in ("POST", "PUT", "PATCH"):
        all_headers["Content-Type"] = "application/json"

    # Combine -H flag with argument to prevent line-break issues
    for key, value in all_headers.items():
        parts.append(f"-H '{key}: {value}'")

    # JSON body - combine -d flag with argument
    if data:
        json_str = json.dumps(data)
        # Escape single quotes in JSON and wrap in single quotes
        json_escaped = json_str.replace("'", "'\\''")
        parts.append(f"-d '{json_escaped}'")

    # URL (quoted)
    parts.append(shlex.quote(url))

    return " \\\n  ".join(parts)


def print_curl(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> None:
    """Print a curl command for an API call."""
    print(generate_curl(method, url, headers, data, params))


# Convenience functions for common services


def files_curl(
    method: str,
    endpoint: str,
    project_id: str,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> str:
    """Generate curl for file-service.

    File-service endpoints use /api/v1/files/... with project_id as query param.
    """
    settings = get_settings()
    url = f"{settings.file_url}/api/v1{endpoint}"
    headers = {"X-Project-ID": project_id}
    # Add project_id to query params
    all_params = {"project_id": project_id, **(params or {})}
    return generate_curl(method, url, headers, data, all_params)


def compute_curl(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> str:
    """Generate curl for compute-service."""
    settings = get_settings()
    url = f"{settings.compute_url}/api/v1{endpoint}"
    return generate_curl(method, url, None, data, params)


def miner_curl(
    method: str,
    endpoint: str,
    project_id: str,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> str:
    """Generate curl for miner-service."""
    settings = get_settings()
    url = f"{settings.miner_url}/api/v1{endpoint}"
    headers = {"X-Project-ID": project_id}
    return generate_curl(method, url, headers, data, params)


def admin_curl(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> str:
    """Generate curl for admin-service."""
    settings = get_settings()
    url = f"{settings.admin_url}/api/v1{endpoint}"
    return generate_curl(method, url, None, data, params)

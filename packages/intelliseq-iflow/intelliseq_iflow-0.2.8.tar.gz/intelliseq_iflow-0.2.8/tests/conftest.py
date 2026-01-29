"""Pytest configuration for CLI E2E tests."""

import os

import pytest


@pytest.fixture
def test_project_id() -> str:
    """Get test project ID from environment."""
    project_id = os.environ.get("FLOW_TEST_PROJECT_ID", "01c965b9-3366-4a09-81f0-dcc88375e76a")
    return project_id


@pytest.fixture
def test_token() -> str | None:
    """Get test PAT token from environment."""
    return os.environ.get("FLOW_TEST_TOKEN")


@pytest.fixture
def test_bucket() -> str:
    """Get test bucket for file operations."""
    return os.environ.get("FLOW_TEST_BUCKET", "bucket-intelliseq-demo")

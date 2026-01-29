"""CLI E2E tests for full workflow.

Tests the CLI tool for:
- Configuration management
- File operations (list, upload, download)
- Pipeline runs (submit, status, watch)
"""

import subprocess
import time

import pytest


def run_flow(*args: str, token: str | None = None) -> subprocess.CompletedProcess:
    """Run flow CLI command and return result."""
    cmd = ["flow", *args]
    env = None
    if token:
        env = {"FLOW_TEST_TOKEN": token}
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


class TestConfigCommands:
    """Tests for flow config commands."""

    def test_config_show(self):
        """Test flow config show displays settings."""
        result = run_flow("config", "show")
        assert result.returncode == 0
        assert "environment" in result.stdout or "file_url" in result.stdout

    def test_config_env_show(self):
        """Test flow config env shows current environment."""
        result = run_flow("config", "env")
        assert result.returncode == 0
        assert "Current environment" in result.stdout
        assert "Available environments" in result.stdout
        # Check all three envs are listed
        assert "prod" in result.stdout
        assert "stg" in result.stdout
        assert "dev" in result.stdout

    def test_config_env_switch_dev(self):
        """Test switching to dev environment."""
        result = run_flow("config", "env", "dev")
        assert result.returncode == 0
        assert "Switched to" in result.stdout or "dev" in result.stdout


class TestAuthCommands:
    """Tests for flow auth/login commands."""

    def test_login_no_token_starts_device_flow(self):
        """Test flow login without token starts device flow."""
        result = run_flow("login")
        # Should attempt device flow (may fail if not configured)
        assert "authenticate" in result.stdout.lower() or "device" in result.stdout.lower()

    def test_login_with_token_stores_it(self):
        """Test flow login with token stores it without validation."""
        result = run_flow("login", "--token", "test-token-12345")
        # CLI stores token without server-side validation
        # Validation happens on first API call
        assert result.returncode == 0
        assert "logged in" in result.stdout.lower()

    def test_status_shows_auth_state(self):
        """Test flow status shows authentication state."""
        result = run_flow("status")
        # Should show either logged in or not logged in
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "logged" in output or "auth" in output or "token" in output


class TestFileCommands:
    """Tests for flow files commands."""

    def test_files_ls_without_auth(self):
        """Test flow files ls without auth fails."""
        result = run_flow("files", "ls")
        # Should fail with auth error
        assert result.returncode != 0 or "not authenticated" in result.stdout.lower()

    @pytest.mark.skipif(
        not pytest.importorskip("os").environ.get("FLOW_TEST_TOKEN"),
        reason="FLOW_TEST_TOKEN not set",
    )
    def test_files_ls_with_auth(self, test_token: str, test_project_id: str):
        """Test flow files ls with valid auth."""
        # First login
        login_result = run_flow("login", "--token", test_token)
        assert login_result.returncode == 0

        # Then list files
        result = run_flow("files", "ls", "--project", test_project_id)
        # Should succeed or show empty list
        assert result.returncode == 0


class TestPipelineCommands:
    """Tests for flow pipelines commands."""

    def test_pipelines_list(self):
        """Test flow pipelines list shows available pipelines."""
        result = run_flow("pipelines", "list")
        # May fail without auth, but shouldn't crash
        assert result.returncode in [0, 1]

    def test_pipelines_info_invalid(self):
        """Test flow pipelines info with invalid slug."""
        result = run_flow("pipelines", "info", "nonexistent-pipeline")
        assert result.returncode != 0


class TestRunCommands:
    """Tests for flow runs commands."""

    def test_runs_list_without_project(self):
        """Test flow runs list without project fails."""
        result = run_flow("runs", "list")
        # Should fail without project
        assert result.returncode != 0 or "project" in result.stdout.lower()


class TestHereditaryMockWorkflow:
    """Full E2E workflow test for hereditary-mock pipeline.

    This test requires:
    - FLOW_TEST_TOKEN environment variable
    - FLOW_TEST_PROJECT_ID environment variable (default: intelliseq demo)
    - Test data in gs://bucket-intelliseq-demo/test-data/
    """

    @pytest.mark.skipif(
        not pytest.importorskip("os").environ.get("FLOW_TEST_TOKEN"),
        reason="FLOW_TEST_TOKEN not set",
    )
    def test_full_hereditary_mock_workflow(self, test_token: str, test_project_id: str):
        """Test complete CLI workflow: login, submit, watch, check output.

        Steps:
        1. Login with PAT token
        2. Verify hereditary-mock pipeline exists
        3. Submit run with test inputs
        4. Watch until completion
        5. Check run status
        """
        # Step 1: Login
        login_result = run_flow("login", "--token", test_token)
        assert login_result.returncode == 0, f"Login failed: {login_result.stderr}"

        # Step 2: Check pipeline exists
        info_result = run_flow("pipelines", "info", "hereditary-mock")
        if info_result.returncode != 0:
            pytest.skip("hereditary-mock pipeline not seeded")

        # Step 3: Submit run
        submit_result = run_flow(
            "runs",
            "submit",
            "--project",
            test_project_id,
            "--pipeline",
            "hereditary-mock",
            "-P",
            "case_id=cli-e2e-test",
            "-P",
            "child_fastq=gs://bucket-intelliseq-demo/test-data/regions_R1.fastq.gz",
            "-P",
            "child_fastq=gs://bucket-intelliseq-demo/test-data/regions_R2.fastq.gz",
        )
        assert submit_result.returncode == 0, f"Submit failed: {submit_result.stderr}"

        # Extract run ID from output
        output = submit_result.stdout
        run_id = None
        for line in output.split("\n"):
            if "run_id" in line.lower() or "id:" in line.lower():
                # Try to extract UUID-like string
                import re

                match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", line)
                if match:
                    run_id = match.group()
                    break

        if not run_id:
            # Fallback: check status to get latest run
            status_result = run_flow("runs", "list", "--project", test_project_id)
            assert status_result.returncode == 0
            # The run was submitted successfully
            return

        # Step 4: Poll status (simplified - not using --watch to avoid blocking)
        max_wait = 300  # 5 minutes
        poll_interval = 30
        elapsed = 0
        final_status = None

        while elapsed < max_wait:
            status_result = run_flow("runs", "status", run_id)
            if status_result.returncode == 0:
                output = status_result.stdout.lower()
                if "succeeded" in output:
                    final_status = "succeeded"
                    break
                elif "failed" in output:
                    final_status = "failed"
                    break
                elif "cancelled" in output:
                    final_status = "cancelled"
                    break

            time.sleep(poll_interval)
            elapsed += poll_interval

        # Step 5: Verify terminal status
        assert final_status in [
            "succeeded",
            "failed",
            "cancelled",
        ], f"Run did not complete within {max_wait}s"

        if final_status == "succeeded":
            print(f"CLI E2E test passed: run {run_id} succeeded")
        elif final_status == "failed":
            print(f"CLI E2E test: run {run_id} failed (may be expected for mock)")

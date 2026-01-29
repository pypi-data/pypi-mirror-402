"""Run commands for iFlow CLI."""

import asyncio
import time

import click

from iflow.api import APIError, ComputeAPIClient
from iflow.config import require_project, resolve_gcs_path, to_relative_path
from iflow.curl import compute_curl


@click.group()
def runs():
    """Manage pipeline runs."""
    pass


@runs.command("list")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.option("-o", "--order-id", help="Filter by order ID")
@click.option("--limit", default=20, help="Maximum runs to display")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def list_runs(project: str | None, order_id: str | None, limit: int, curl: bool):
    """List runs for a project.

    \b
    Examples:
      iflow runs list
      iflow runs list --order-id ORDER_ID
    """
    project_id = require_project(project)

    if curl:
        params = {"project_id": project_id, "limit": str(limit)}
        if order_id:
            params["order_id"] = order_id
        print(compute_curl("GET", "/runs", params=params))
        return

    async def _list():
        client = ComputeAPIClient()
        try:
            if order_id:
                runs_list = await client.list_runs_by_order(order_id)
            else:
                runs_list = await client.list_runs(project_id, limit=limit)

            if not runs_list:
                click.echo("No runs found.")
                return

            # Print header
            click.echo(f"{'ID':<40} {'NAME':<35} {'STATUS':<12}")
            click.echo("-" * 90)

            for r in runs_list:
                click.echo(f"{r.id:<40} {r.name:<35} {r.status:<12}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_list())


@runs.command("last")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.option("--id", "show_id", is_flag=True, help="Output only the run ID (for scripting)")
@click.option("--name", "show_name", is_flag=True, help="Output only the run name")
@click.option("--output", "show_output", is_flag=True, help="Output only the output path")
@click.option("--status-filter", help="Filter by status (e.g., succeeded, failed)")
def last_run(
    project: str | None,
    show_id: bool,
    show_name: bool,
    show_output: bool,
    status_filter: str | None,
):
    """Get the most recent run.

    Useful for scripting to get the last run ID, name, or output path.

    \b
    Examples:
      iflow runs last
      iflow runs last --id
      RUN_ID=$(iflow runs last --id)
      iflow runs last --output --status-filter succeeded
    """
    project_id = require_project(project)

    async def _last():
        client = ComputeAPIClient()
        try:
            runs_list = await client.list_runs(project_id, limit=20)

            if status_filter:
                runs_list = [r for r in runs_list if r.status == status_filter]

            if not runs_list:
                if status_filter:
                    click.echo(f"No runs found with status '{status_filter}'.", err=True)
                else:
                    click.echo("No runs found.", err=True)
                raise SystemExit(1)

            run = runs_list[0]  # Most recent

            # Output mode for scripting
            if show_id:
                click.echo(run.id)
            elif show_name:
                click.echo(run.name)
            elif show_output:
                if run.output_path:
                    click.echo(to_relative_path(run.output_path))
                else:
                    click.echo("", err=True)  # Empty if no output
                    raise SystemExit(1)
            else:
                # Full output
                click.echo(f"Run: {run.name}")
                click.echo(f"  ID: {run.id}")
                click.echo(f"  Status: {run.status}")
                if run.output_path:
                    click.echo(f"  Output: {to_relative_path(run.output_path)}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_last())


@runs.command("submit")
@click.option("-p", "--project", help="Project ID (uses default if not specified)")
@click.option("--pipeline", required=True, help="Pipeline slug (e.g., hereditary-mock)")
@click.option("--pipeline-version", "-V", help="Pipeline version (e.g., 1.0.0)")
@click.option("--order-id", "-o", help="Order ID to associate with this run (from miner-service)")
@click.option("--param", "-P", multiple=True, help="Parameter in KEY=VALUE format")
@click.option("--tag", "-t", multiple=True, help="Tag for the run")
@click.option("--profile", help="Override Nextflow profile")
@click.option("--callback-url", help="URL for callback on completion/failure (LIS)")
@click.option("--watch", is_flag=True, help="Watch run status after submission")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def submit_run(
    project: str | None,
    pipeline: str,
    pipeline_version: str | None,
    order_id: str | None,
    param: tuple[str, ...],
    tag: tuple[str, ...],
    profile: str | None,
    callback_url: str | None,
    watch: bool,
    curl: bool,
):
    """Submit a new pipeline run.

    \b
    Examples:
      iflow runs submit --pipeline hereditary-mock \\
        -P case_id=patient-001 \\
        -P child_fastq=data/R1.fastq.gz \\
        -P child_fastq=data/R2.fastq.gz

      iflow runs submit --pipeline hereditary-mock -V 1.0.0 \\
        --order-id ORDER_ID -P case_id=patient-001 --watch

      iflow runs submit --pipeline nextflow-minimal \\
        -P analysis_name=test --watch

      # With callback URL for LIS integration
      iflow runs submit --pipeline hereditary-mock \\
        -P case_id=patient-001 \\
        --callback-url https://lis.example.com/api/results
    """
    project_id = require_project(project)

    # Parse parameters - handle multiple values for same key
    # File paths are auto-resolved: relative paths get bucket prefix
    params = {}
    for p in param:
        if "=" not in p:
            click.echo(f"Invalid parameter format: {p} (use KEY=VALUE)", err=True)
            raise SystemExit(1)
        key, value = p.split("=", 1)

        # Resolve file paths (looks like a path if contains / or common extensions)
        file_exts = (".gz", ".fastq", ".fq", ".vcf", ".bam", ".cram", ".bed")
        if "/" in value or value.endswith(file_exts):
            value = resolve_gcs_path(value)

        if key in params:
            # Multiple values for same key - convert to list
            if isinstance(params[key], list):
                params[key].append(value)
            else:
                params[key] = [params[key], value]
        else:
            params[key] = value

    if curl:
        # For curl output, we need pipeline_id but we don't have it yet
        # Show with pipeline slug and note that it needs to be resolved
        data = {
            "project_id": project_id,
            "pipeline_slug": pipeline,
            "params": params,
        }
        if pipeline_version:
            data["pipeline_version"] = pipeline_version
        if order_id:
            data["order_id"] = order_id
        if tag:
            data["tags"] = list(tag)
        if profile:
            data["profile"] = profile
        if callback_url:
            data["callback_url"] = callback_url
        print("# Note: pipeline_slug needs to be resolved to pipeline_id first")
        version_param = f"?version={pipeline_version}" if pipeline_version else ""
        print(f"# GET {compute_curl('GET', f'/pipelines/slug/{pipeline}{version_param}')}")
        print()
        print(compute_curl("POST", "/runs", data=data))
        return

    async def _submit():
        client = ComputeAPIClient()
        try:
            # Get pipeline ID from slug (and optional version)
            pipeline_obj = await client.get_pipeline(pipeline, pipeline_version)
            pipeline_id = pipeline_obj.id

            # Submit run
            run = await client.submit_run(
                project_id=project_id,
                pipeline_id=pipeline_id,
                order_id=order_id,
                params=params,
                tags=list(tag),
                profile=profile,
                callback_url=callback_url,
            )

            click.echo("Run submitted successfully!")
            click.echo(f"  ID: {run.id}")
            click.echo(f"  Name: {run.name}")
            click.echo(f"  Status: {run.status}")

            if watch:
                click.echo("\nWatching run status (Ctrl+C to stop)...")
                await _watch_run(client, run.id)

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_submit())


@runs.command("status")
@click.argument("run_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def run_status(run_id: str, curl: bool):
    """Get status of a run.

    RUN_ID is the run identifier.
    """
    if curl:
        print(compute_curl("GET", f"/runs/{run_id}"))
        return

    async def _status():
        client = ComputeAPIClient()
        try:
            run = await client.get_run(run_id)

            click.echo(f"Run: {run.name}")
            click.echo(f"  ID: {run.id}")
            click.echo(f"  Status: {run.status}")
            click.echo(f"  Pipeline ID: {run.pipeline_id}")
            if run.order_id:
                click.echo(f"  Order ID: {run.order_id}")
            click.echo(f"  Profile: {run.profile or 'default'}")

            if run.created_at:
                click.echo(f"  Created: {run.created_at}")
            if run.started_at:
                click.echo(f"  Started: {run.started_at}")
            if run.finished_at:
                click.echo(f"  Finished: {run.finished_at}")

            if run.output_path:
                click.echo(f"  Output: {to_relative_path(run.output_path)}")
            if run.error_message:
                click.echo(f"  Error: {run.error_message}")

            if run.params:
                click.echo("  Parameters:")
                for k, v in run.params.items():
                    click.echo(f"    {k}: {v}")

            if run.tags:
                click.echo(f"  Tags: {', '.join(run.tags)}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_status())


@runs.command("cancel")
@click.argument("run_id")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
@click.confirmation_option(prompt="Are you sure you want to cancel this run?")
def cancel_run(run_id: str, curl: bool):
    """Cancel a running or queued run.

    RUN_ID is the run identifier.
    """
    if curl:
        print(compute_curl("POST", f"/runs/{run_id}/cancel"))
        return

    async def _cancel():
        client = ComputeAPIClient()
        try:
            await client.cancel_run(run_id)
            click.echo(f"Run {run_id} cancelled.")
        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_cancel())


@runs.command("outputs")
@click.argument("run_id")
@click.option("-d", "--download", help="Download specific output by name")
@click.option("-o", "--output", help="Output file path (with --download)")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def run_outputs(run_id: str, download: str | None, output: str | None, curl: bool):
    """List semantic outputs of a run, or download by name.

    Shows outputs mapped from meta.json definitions.
    Only available for WDL runs that have completed.

    \b
    Examples:
      iflow runs outputs RUN_ID
      iflow runs outputs RUN_ID -d annotated_vcf_gz
      iflow runs outputs RUN_ID -d top20_tsv -o results.tsv
    """
    if curl:
        # Show curl command regardless of download flag
        print(compute_curl("GET", f"/runs/{run_id}/outputs"))
        if download:
            print("\n# To download a specific output, use the path from the response above with:")
            print("# iflow files download <path> --curl")
        return

    async def _outputs():
        client = ComputeAPIClient()
        try:
            response = await client.get_run_outputs(run_id)

            if not response.outputs:
                if response.message:
                    click.echo(f"No outputs: {response.message}")
                else:
                    click.echo("No outputs found.")
                return

            if download:
                # Find output by name
                matching = [o for o in response.outputs if o.name == download]
                if not matching:
                    available = ", ".join(o.name for o in response.outputs)
                    click.echo(f"Error: Output '{download}' not found.", err=True)
                    click.echo(f"Available outputs: {available}", err=True)
                    raise SystemExit(1)

                output_info = matching[0]
                if not output_info.path:
                    click.echo(f"Error: Output '{download}' has no path.", err=True)
                    raise SystemExit(1)

                # Download the file
                from iflow.api import FlowAPIClient
                from iflow.config import require_project
                from pathlib import Path

                file_client = FlowAPIClient()
                project_id = require_project(None)

                # Extract relative path from gs:// URL
                gcs_path = output_info.path
                if gcs_path.startswith("gs://"):
                    # Format: gs://bucket/path/to/file
                    parts = gcs_path.replace("gs://", "").split("/", 1)
                    if len(parts) > 1:
                        relative_path = parts[1]
                    else:
                        click.echo(f"Error: Invalid GCS path: {gcs_path}", err=True)
                        raise SystemExit(1)
                else:
                    relative_path = gcs_path

                click.echo(f"Downloading {download}...")
                url = await file_client.get_download_url(project_id, relative_path)

                # Determine output filename
                output_path = output or Path(gcs_path).name
                await file_client.download_file(url, output_path)
                click.echo(f"Downloaded: {output_path}")
            else:
                # List outputs
                click.echo(f"{'NAME':<20} {'TYPE':<10} {'PATH'}")
                click.echo("-" * 80)

                for out in response.outputs:
                    path = to_relative_path(out.path) or "-"
                    click.echo(f"{out.name:<20} {out.type:<10} {path}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_outputs())


@runs.command("watch")
@click.argument("run_id")
@click.option("--interval", default=10, help="Polling interval in seconds")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def watch_run(run_id: str, interval: int, curl: bool):
    """Watch run status until completion.

    RUN_ID is the run identifier.
    """
    if curl:
        print(f"# This command polls the following endpoint every {interval} seconds:")
        print(compute_curl("GET", f"/runs/{run_id}"))
        return

    async def _watch():
        client = ComputeAPIClient()
        try:
            await _watch_run(client, run_id, interval)
        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_watch())


async def _watch_run(client: ComputeAPIClient, run_id: str, interval: int = 10):
    """Watch run status until terminal state."""
    terminal_statuses = {"succeeded", "failed", "cancelled"}
    last_status = None

    try:
        while True:
            run = await client.get_run(run_id)

            if run.status != last_status:
                timestamp = time.strftime("%H:%M:%S")
                click.echo(f"[{timestamp}] Status: {run.status}")
                last_status = run.status

                if run.status == "running" and run.started_at:
                    click.echo(f"           Started: {run.started_at}")

            if run.status in terminal_statuses:
                click.echo()
                if run.status == "succeeded":
                    click.echo("Run completed successfully!")
                    if run.output_path:
                        click.echo(f"Output: {to_relative_path(run.output_path)}")
                elif run.status == "failed":
                    click.echo(f"Run failed: {run.error_message or 'Unknown error'}")
                else:
                    click.echo("Run was cancelled.")
                break

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\nStopped watching (run continues in background).")

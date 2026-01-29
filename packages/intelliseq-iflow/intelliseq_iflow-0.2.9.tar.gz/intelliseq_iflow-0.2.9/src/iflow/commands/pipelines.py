"""Pipeline commands for iFlow CLI."""

import asyncio
import re
from urllib.parse import urlparse

import click
import httpx

from iflow.api import APIError, ComputeAPIClient
from iflow.curl import compute_curl


def derive_meta_url(wdl_url: str) -> str:
    """Derive meta.json URL from WDL URL.

    Example:
        Input:  .../hereditary-merged-mock.wdl?token=1234
        Output: .../meta.json?token=1234
    """
    # Parse URL
    parsed = urlparse(wdl_url)
    path = parsed.path

    # Replace .wdl filename with meta.json
    if path.endswith(".wdl"):
        # Find the last / and replace the filename
        dir_path = path.rsplit("/", 1)[0]
        new_path = f"{dir_path}/meta.json"
    else:
        # Not a .wdl file, just append meta.json
        new_path = f"{path}/meta.json"

    # Reconstruct URL with same query params
    result = f"{parsed.scheme}://{parsed.netloc}{new_path}"
    if parsed.query:
        result += f"?{parsed.query}"

    return result


async def fetch_meta_json(meta_url: str) -> dict | None:
    """Fetch meta.json from URL and parse it."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(meta_url, timeout=30.0)
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None


def derive_slug_from_url(wdl_url: str) -> str:
    """Derive slug from WDL URL path.

    Example:
        Input:  .../pipelines/hereditary-merged-mock/hereditary-merged-mock.wdl
        Output: hereditary-merged-mock
    """
    parsed = urlparse(wdl_url)
    path = parsed.path

    # Get filename without extension
    filename = path.rsplit("/", 1)[-1]
    if filename.endswith(".wdl"):
        filename = filename[:-4]

    # Slugify: lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", filename.lower())
    slug = slug.strip("-")

    return slug


@click.group()
def pipelines():
    """Manage pipelines."""
    pass


@pipelines.command("list")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def list_pipelines(curl: bool):
    """List available pipelines."""
    if curl:
        print(compute_curl("GET", "/pipelines"))
        return

    async def _list():
        client = ComputeAPIClient()
        try:
            pipelines_list = await client.list_pipelines()

            if not pipelines_list:
                click.echo("No pipelines found.")
                return

            # Print header
            click.echo(f"{'SLUG':<25} {'VERSION':<10} {'NAME':<25} {'MODE':<20}")
            click.echo("-" * 85)

            for p in pipelines_list:
                click.echo(f"{p.slug:<25} {p.version:<10} {p.name:<25} {p.execution_mode:<20}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_list())


@pipelines.command("info")
@click.argument("slug")
@click.option(
    "-V", "--version", "pipeline_version", help="Specific version (e.g., 1.0.0)"
)
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def pipeline_info(slug: str, pipeline_version: str | None, curl: bool):
    """Get details about a pipeline.

    SLUG is the pipeline identifier (e.g., 'hereditary-mock').

    \b
    Examples:
      iflow pipelines info hereditary-mock
      iflow pipelines info hereditary-mock -V 1.0.0
    """
    if curl:
        version_param = f"?version={pipeline_version}" if pipeline_version else ""
        print(compute_curl("GET", f"/pipelines/slug/{slug}{version_param}"))
        return

    async def _info():
        client = ComputeAPIClient()
        try:
            p = await client.get_pipeline(slug, pipeline_version)

            click.echo(f"Pipeline: {p.name}")
            click.echo(f"  Slug: {p.slug}")
            click.echo(f"  Version: {p.version}")
            click.echo(f"  ID: {p.id}")
            click.echo(f"  Description: {p.description or 'N/A'}")
            click.echo(f"  Source Type: {p.source_type}")
            click.echo(f"  Execution Mode: {p.execution_mode}")
            click.echo(f"  Default Profile: {p.default_profile}")
            click.echo(f"  Active: {'Yes' if p.is_active else 'No'}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_info())


@pipelines.command("versions")
@click.argument("slug")
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def pipeline_versions(slug: str, curl: bool):
    """List all versions of a pipeline.

    SLUG is the pipeline identifier (e.g., 'hereditary-mock').

    \b
    Examples:
      iflow pipelines versions hereditary-mock
    """
    if curl:
        print(compute_curl("GET", f"/pipelines/slug/{slug}/versions"))
        return

    async def _versions():
        client = ComputeAPIClient()
        try:
            versions = await client.list_pipeline_versions(slug)

            if not versions:
                click.echo(f"Pipeline '{slug}' not found.")
                return

            click.echo(f"Versions of '{slug}':")
            click.echo()
            click.echo(f"{'VERSION':<12} {'NAME':<30} {'ACTIVE'}")
            click.echo("-" * 50)

            for p in versions:
                active = "Yes" if p.is_active else "No"
                click.echo(f"{p.version:<12} {p.name:<30} {active}")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_versions())


@pipelines.command("describe")
@click.argument("slug")
@click.option(
    "-V", "--version", "pipeline_version", help="Specific version (e.g., 1.0.0)"
)
def describe_pipeline(slug: str, pipeline_version: str | None):
    """Show inputs and outputs for a pipeline.

    Fetches meta.json to display available inputs and expected outputs.

    \b
    Examples:
      iflow pipelines describe hereditary-mock
      iflow pipelines describe hereditary-mock -V 1.0.0
    """
    async def _describe():
        client = ComputeAPIClient()
        try:
            # Get pipeline details
            p = await client.get_pipeline(slug, pipeline_version)

            click.echo(f"Pipeline: {p.name}")
            click.echo(f"  Slug: {p.slug}")
            click.echo(f"  Version: {p.version}")
            click.echo(f"  Mode: {p.execution_mode}")
            click.echo()

            # Try to fetch meta.json from properties or derive from source_url
            meta_url = None
            if p.properties:
                meta_url = p.properties.get("meta_url")

            # If no meta_url in properties, derive from source_url
            if not meta_url and p.source_url:
                meta_url = derive_meta_url(p.source_url)
                click.echo("[dim]Derived meta.json URL from source[/dim]")

            if not meta_url:
                click.echo("[yellow]Cannot determine meta.json URL[/yellow]")
                return

            meta = await fetch_meta_json(meta_url)

            if not meta:
                click.echo("[yellow]Could not fetch meta.json[/yellow]")
                return

            # Display inputs - support both array format and flat input_* keys
            inputs = meta.get("inputs", [])

            # If no inputs array, look for input_* keys (legacy format)
            if not inputs:
                for key, value in meta.items():
                    if key.startswith("input_") and isinstance(value, dict):
                        inputs.append({"name": key, **value})

            if inputs:
                click.echo("INPUTS:")
                click.echo("-" * 70)
                for inp in inputs:
                    name = inp.get("name", "unknown")
                    wdl_type = inp.get("wdl_type", inp.get("type", "?"))
                    required = "required" if inp.get("required", False) else "optional"
                    desc = inp.get("description", "")[:50]

                    # Extract just the input name (remove prefix)
                    if name.startswith("input_"):
                        name = name[6:]

                    click.echo(f"  {name:<25} {wdl_type:<15} [{required}]")
                    if desc:
                        click.echo(f"    {desc}")
            else:
                click.echo("INPUTS: (none defined in meta.json)")

            click.echo()

            # Display outputs - support both array format and flat output_* keys
            outputs = meta.get("outputs", [])

            # If no outputs array, look for output_* keys (legacy format)
            if not outputs:
                for key, value in meta.items():
                    if key.startswith("output_") and isinstance(value, dict):
                        outputs.append({"name": key, **value})

            if outputs:
                click.echo("OUTPUTS:")
                click.echo("-" * 70)
                for out in outputs:
                    name = out.get("name", "unknown")
                    wdl_type = out.get("wdl_type", out.get("type", "?"))
                    desc = out.get("description", "")[:50]

                    # Extract just the output name (remove prefix)
                    if name.startswith("output_"):
                        name = name[7:]

                    click.echo(f"  {name:<25} {wdl_type:<15}")
                    if desc:
                        click.echo(f"    {desc}")
            else:
                click.echo("OUTPUTS: (none defined in meta.json)")

        except APIError as e:
            click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_describe())


@pipelines.command("add")
@click.option("--url", required=True, help="URL to WDL/Nextflow workflow file")
@click.option("--name", help="Pipeline display name (auto-detected from meta.json)")
@click.option("--slug", help="URL-safe identifier (auto-derived from URL)")
@click.option("-V", "--version", "pipeline_version", help="Version (auto-detected from meta.json)")
@click.option("--description", help="Pipeline description (auto-detected from meta.json)")
@click.option("--force", "-f", is_flag=True, help="Overwrite if pipeline version exists")
@click.option(
    "--type", "source_type", default="gitlab",
    type=click.Choice(["gitlab", "github", "nfcore"]),
    help="Source type (default: gitlab)",
)
@click.option(
    "--mode", "execution_mode", default="direct_wdl",
    type=click.Choice(["direct_wdl", "direct_nextflow", "container_entrypoint"]),
    help="Execution mode (default: direct_wdl)",
)
@click.option("--profile", default="local", help="Default profile (default: local)")
@click.option(
    "--container", default="broadinstitute/cromwell:86",
    help="Container image (default: broadinstitute/cromwell:86)",
)
def add_pipeline(
    url: str,
    name: str | None,
    slug: str | None,
    pipeline_version: str | None,
    description: str | None,
    force: bool,
    source_type: str,
    execution_mode: str,
    profile: str,
    container: str,
):
    """Add a new pipeline from URL.

    Automatically detects version and metadata from meta.json in the same directory.

    \b
    Examples:
      iflow pipelines add --url https://workflows.example.com/.../workflow.wdl
      iflow pipelines add --url https://workflows.example.com/.../workflow.wdl --force
      iflow pipelines add --url https://workflows.example.com/.../workflow.wdl -V 2.0.0
    """
    async def _add():
        # Derive meta.json URL and try to fetch it
        meta_url = derive_meta_url(url)
        click.echo(f"Fetching metadata from: {meta_url}")

        meta = await fetch_meta_json(meta_url)

        # Use values from meta.json if not provided via CLI
        final_name = name
        final_version = pipeline_version
        final_description = description
        final_slug = slug or derive_slug_from_url(url)

        properties = {"source_url": url}

        if meta:
            click.echo("[green]Found meta.json[/green]")
            if not final_name and "name" in meta:
                final_name = meta["name"]
            if not final_version and "version" in meta:
                final_version = meta["version"]
            if not final_description:
                # Try description_short first, then description_long
                final_description = meta.get("description_short") or meta.get(
                    "description_long", ""
                )[:500]

            # Store meta_url and author info in properties
            properties["meta_url"] = meta_url
            if "author" in meta:
                properties["author"] = meta["author"]
            if "copyright" in meta:
                properties["copyright"] = meta["copyright"]
            if "tag" in meta:
                properties["tag"] = meta["tag"]
            if "version_history" in meta:
                properties["version_history"] = meta["version_history"]
        else:
            click.echo("[yellow]meta.json not found, using CLI arguments[/yellow]")

        # Validate required fields
        if not final_name:
            click.echo("Error: --name is required (no meta.json found)", err=True)
            raise SystemExit(1)

        if not final_version:
            final_version = "1.0.0"
            click.echo(f"[yellow]No version found, using default: {final_version}[/yellow]")

        click.echo("\nAdding pipeline:")
        click.echo(f"  Name: {final_name}")
        click.echo(f"  Slug: {final_slug}")
        click.echo(f"  Version: {final_version}")
        click.echo(f"  Mode: {execution_mode}")
        if force:
            click.echo("  Force: Yes (will overwrite if exists)")

        client = ComputeAPIClient()
        try:
            p = await client.create_pipeline(
                name=final_name,
                slug=final_slug,
                version=final_version,
                source_type=source_type,
                source_url=url,
                execution_mode=execution_mode,
                default_profile=profile,
                default_container_image=container,
                description=final_description,
                properties=properties,
                force=force,
            )

            click.echo()
            click.echo("[green]Pipeline added successfully![/green]")
            click.echo(f"  ID: {p.id}")
            click.echo(f"  Slug: {p.slug}")
            click.echo(f"  Version: {p.version}")

        except APIError as e:
            if "already exists" in str(e):
                click.echo(f"\n[red]Error:[/red] {e}", err=True)
                click.echo("Use --force to overwrite.", err=True)
            else:
                click.echo(f"Error: {e}", err=True)
            raise SystemExit(1)

    asyncio.run(_add())

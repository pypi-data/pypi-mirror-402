"""Configuration commands."""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from iflow.api import AdminAPIClient, APIError
from iflow.config import (
    ENVIRONMENTS,
    clear_project_context,
    get_settings,
    load_config,
    normalize_bucket_name,
    save_config,
    set_project_context,
)
from iflow.curl import admin_curl

console = Console()


@click.group()
def config():
    """Configuration management."""
    pass


@config.command("show")
def show_config():
    """Show current configuration."""
    settings = get_settings()
    file_config = load_config()

    # Show project context first if set
    if settings.project_id:
        console.print("[bold]Current Project Context[/bold]")
        console.print(f"  Organization: [cyan]{settings.org_name or 'Unknown'}[/cyan]")
        console.print(f"  Project: [cyan]{settings.project_name or 'Unknown'}[/cyan]")
        console.print(f"  Project ID: [dim]{settings.project_id}[/dim]")
        console.print()
    else:
        console.print("[yellow]No default project set.[/yellow]")
        console.print("Run [cyan]flow config select-project[/cyan] to select one.\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_column("Source")

    # Show key settings
    config_items = [
        ("environment", settings.environment),
        ("file_url", settings.file_url),
        ("compute_url", settings.compute_url),
        ("admin_url", settings.admin_url),
        ("miner_url", settings.miner_url),
        ("zitadel_issuer", settings.zitadel_issuer),
    ]

    for key, value in config_items:
        source = "[green]config file[/green]" if key in file_config else "[dim]default[/dim]"
        table.add_row(key, value, source)

    console.print(table)


@config.command("env")
@click.argument("environment", required=False)
def set_env(environment: str | None):
    """
    Set or show the current environment.

    \b
    Available environments:
      prod  - Production (iflow.intelliseq.com)
      stg   - Staging (stg.iflow.intelliseq.com)
      dev   - Development (flow.labpgx.com - nginx proxy to localhost)

    \b
    Examples:
      iflow config env         # Show current environment
      iflow config env dev     # Switch to dev environment
      iflow config env prod    # Switch to production
    """
    file_config = load_config()

    if environment is None:
        # Show current environment
        current = file_config.get("environment", "dev")
        env_info = ENVIRONMENTS.get(current, {})
        console.print(f"Current environment: [cyan]{current}[/cyan]")
        console.print(f"  Domain: {env_info.get('domain', 'unknown')}")
        console.print()
        console.print("Available environments:")
        for env_key, env_data in ENVIRONMENTS.items():
            marker = "[green]●[/green]" if env_key == current else "[dim]○[/dim]"
            console.print(f"  {marker} {env_key:6} - {env_data['name']} ({env_data['domain']})")
        return

    if environment not in ENVIRONMENTS:
        console.print(f"[red]Unknown environment:[/red] {environment}")
        console.print(f"Available: {', '.join(ENVIRONMENTS.keys())}")
        raise SystemExit(1)

    # Apply environment preset
    env_preset = ENVIRONMENTS[environment]
    file_config["environment"] = environment
    file_config["file_url"] = env_preset["file_url"]
    file_config["compute_url"] = env_preset["compute_url"]
    file_config["admin_url"] = env_preset["admin_url"]
    file_config["miner_url"] = env_preset["miner_url"]
    file_config["api_url"] = env_preset["file_url"]  # Legacy alias
    file_config["zitadel_issuer"] = env_preset["zitadel_issuer"]
    file_config["zitadel_client_id"] = env_preset["zitadel_client_id"]

    # Clear project context when switching environments
    file_config.pop("project_id", None)
    file_config.pop("project_name", None)
    file_config.pop("org_id", None)
    file_config.pop("org_name", None)

    save_config(file_config)

    console.print(f"[green]Switched to {env_preset['name']} ({environment})[/green]")
    console.print(f"  File service:    {env_preset['file_url']}")
    console.print(f"  Compute service: {env_preset['compute_url']}")
    console.print(f"  Admin service:   {env_preset['admin_url']}")
    console.print(f"  Miner service:   {env_preset['miner_url']}")
    console.print()
    console.print("[yellow]Note: Project context cleared. Run 'iflow config select-project' to select a project.[/yellow]")


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str):
    """Set a configuration value."""
    valid_keys = ["file_url", "compute_url", "admin_url", "api_url", "zitadel_issuer", "zitadel_client_id"]

    if key not in valid_keys:
        console.print(f"[red]Invalid key:[/red] {key}")
        console.print(f"Valid keys: {', '.join(valid_keys)}")
        raise SystemExit(1)

    file_config = load_config()
    file_config[key] = value
    save_config(file_config)

    console.print(f"[green]Set {key}=[/green]{value}")


@config.command("reset")
def reset_config():
    """Reset configuration to defaults."""
    save_config({})
    console.print("[green]Configuration reset to defaults.[/green]")


@config.command("select-project")
@click.argument("project_id", required=False)
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def select_project(project_id: str | None, curl: bool):
    """
    Select default project for CLI commands.

    If PROJECT_ID is not provided, shows interactive selection.

    \b
    Examples:
      iflow config select-project                    # Interactive selection
      iflow config select-project PROJECT_ID        # Direct selection
    """
    if curl:
        print(admin_curl("GET", "/projects"))
        return

    async def _select():
        client = AdminAPIClient()

        try:
            # Fetch available projects
            projects = await client.list_projects()

            if not projects:
                console.print("[red]No projects available.[/red]")
                console.print("Ask your administrator to create a project.")
                raise SystemExit(1)

            if project_id:
                # Direct selection by ID
                selected = None
                for p in projects:
                    if p.id == project_id or p.slug == project_id:
                        selected = p
                        break

                if not selected:
                    console.print(f"[red]Project not found:[/red] {project_id}")
                    console.print("\nAvailable projects:")
                    for p in projects:
                        console.print(f"  {p.id}  {p.name} ({p.org_name})")
                    raise SystemExit(1)

            else:
                # Interactive selection
                console.print("[bold]Available Projects[/bold]\n")

                # Group by organization
                orgs: dict[str, list] = {}
                for p in projects:
                    if p.org_name not in orgs:
                        orgs[p.org_name] = []
                    orgs[p.org_name].append(p)

                idx = 1
                project_map = {}
                for org_name, org_projects in orgs.items():
                    console.print(f"[cyan]{org_name}[/cyan]")
                    for p in org_projects:
                        console.print(f"  [{idx}] {p.name}")
                        project_map[idx] = p
                        idx += 1
                    console.print()

                # Prompt for selection
                console.print("Enter project number (or 'q' to cancel): ", end="")
                choice = input().strip()

                if choice.lower() == "q":
                    console.print("Cancelled.")
                    return

                try:
                    choice_num = int(choice)
                    if choice_num not in project_map:
                        console.print("[red]Invalid selection.[/red]")
                        raise SystemExit(1)
                    selected = project_map[choice_num]
                except ValueError:
                    console.print("[red]Invalid input.[/red]")
                    raise SystemExit(1)

            # Save selection
            set_project_context(
                project_id=selected.id,
                project_name=selected.name,
                org_id=selected.org_id,
                org_name=selected.org_name,
                bucket_name=selected.bucket_name,
            )

            console.print()
            console.print(f"[green]Selected project:[/green] {selected.name}")
            console.print(f"  Organization: {selected.org_name}")
            console.print(f"  Project ID: {selected.id}")
            console.print()
            console.print("You can now run commands without specifying -p/--project.")
            console.print("File paths are relative to your project.")

        except APIError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)

    asyncio.run(_select())


@config.command("clear-project")
def clear_project():
    """Clear the saved project selection."""
    clear_project_context()
    console.print("[green]Project context cleared.[/green]")
    console.print("You will need to specify -p/--project for each command.")

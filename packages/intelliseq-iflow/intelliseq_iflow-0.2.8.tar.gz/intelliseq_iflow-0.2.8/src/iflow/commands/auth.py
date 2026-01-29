"""Authentication commands."""

import asyncio

import click
from rich.console import Console

from iflow.auth import (
    AuthError,
    TokenInfo,
    clear_token,
    device_flow_login,
    get_stored_token,
    is_token_expired,
    password_login,
    store_token,
)
from iflow.config import (
    ENVIRONMENTS,
    apply_environment,
    normalize_bucket_name,
    set_project_context,
)

console = Console()


async def detect_environment_by_api(access_token: str) -> str | None:
    """Detect environment by trying token against each environment's API."""
    import httpx

    for env_key, env_config in ENVIRONMENTS.items():
        admin_url = env_config["admin_url"]
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{admin_url}/api/v1/projects",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if response.status_code == 200:
                    return env_key
        except Exception:
            continue
    return None


async def auto_configure_after_login(
    access_token: str, skip_env_detection: bool = False
) -> None:
    """Auto-configure environment and project after successful login."""
    from iflow.api import AdminAPIClient, APIError

    # 1. Auto-detect environment by probing APIs (skip if already selected via prompt)
    if not skip_env_detection:
        detected_env = await detect_environment_by_api(access_token)

        if detected_env:
            apply_environment(detected_env)
            env_name = ENVIRONMENTS[detected_env]["name"]
            console.print(f"[dim]Environment:[/dim] {env_name} (auto-detected)")

    # 3. Try to auto-select project if only one available
    try:
        client = AdminAPIClient(token=access_token)
        projects = await client.list_projects()

        if len(projects) == 1:
            p = projects[0]
            set_project_context(p.id, p.name, p.org_id, p.org_name, p.bucket_name)
            console.print(f"[dim]Project:[/dim] {p.name} (auto-selected)")
        elif len(projects) > 1:
            console.print(f"[dim]Found {len(projects)} projects.[/dim]")
            console.print("Run [cyan]iflow config select-project[/cyan] to choose one.")
        else:
            console.print("[dim]No projects available.[/dim]")
    except APIError:
        # Silently skip auto-configuration if API fails
        pass


def prompt_environment() -> str:
    """Prompt user to select environment for login."""
    console.print("\n[bold]Select environment:[/bold]")
    env_list = list(ENVIRONMENTS.items())
    for i, (key, env) in enumerate(env_list, 1):
        console.print(f"  {i}. {env['name']} ({key})")

    while True:
        choice = console.input("\nEnter choice [1-3]: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(env_list):
                return env_list[idx][0]
        except ValueError:
            pass
        console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/red]")


@click.command()
@click.option("--email", "-e", envvar="FLOW_EMAIL", help="Email (or FLOW_EMAIL env)")
@click.option("--password", "-p", envvar="FLOW_PASSWORD", help="Password (or FLOW_PASSWORD env)")
@click.option("--token", "-t", envvar="FLOW_TOKEN", help="PAT for headless/CI auth")
@click.option(
    "--env",
    type=click.Choice(["prod", "stg", "dev"]),
    default="stg",
    help="Environment (default: stg)",
)
@click.option("--curl", is_flag=True, help="Output curl command instead of executing")
def login(
    email: str | None, password: str | None, token: str | None, env: str, curl: bool
):
    """
    Login to Flow.

    \b
    By default, opens browser to Admin Console (staging) to create a PAT token.
    Use --token option to authenticate with an existing PAT.

    \b
    Examples:
      iflow login                           # Opens browser to create PAT (staging)
      iflow login --env prod                # Use production environment
      iflow login --token YOUR_PAT          # PAT auth (recommended)
      FLOW_TOKEN=YOUR_PAT iflow login       # Via env var
    """
    from iflow.config import get_settings

    # For interactive login, use selected environment and recommend PAT tokens
    if not token and not curl:
        apply_environment(env)

        # Build CLI tokens URL for selected environment
        admin_url = ENVIRONMENTS[env]["admin_url"]
        cli_tokens_url = f"{admin_url}/account/cli-tokens"
        env_name = ENVIRONMENTS[env]["name"]

        console.print(f"[dim]Environment: {env_name}[/dim]")

        console.print()
        console.print("[bold]Personal Access Tokens (PAT) recommended for CLI access.[/bold]")
        console.print()
        console.print("To create a token:")
        console.print(f"  1. Visit: [cyan]{cli_tokens_url}[/cyan]")
        console.print("  2. Log in to Admin Console")
        console.print("  3. Click 'Create Token'")
        console.print("  4. Copy the token and run:")
        console.print("     [cyan]iflow login --token YOUR_TOKEN[/cyan]")
        console.print()

        # Try to open browser
        import webbrowser

        try:
            webbrowser.open(cli_tokens_url)
            console.print("[dim]Opening browser...[/dim]")
        except Exception:
            pass

        return

    settings = get_settings()

    if curl:
        if token:
            console.print("[yellow]Note:[/yellow] PAT login doesn't make an API call.")
            console.print("The token is stored locally for subsequent requests.")
            return

        if email and password:
            # Show ROPC token request
            console.print("# Password login (ROPC grant)")
            console.print("curl -s -X POST \\")
            console.print(f"  '{settings.zitadel_issuer}/oauth/v2/token' \\")
            console.print("  -d 'grant_type=password' \\")
            console.print(f"  -d 'client_id={settings.zitadel_client_id}' \\")
            console.print(f"  -d 'username={email}' \\")
            console.print("  -d 'password=YOUR_PASSWORD' \\")
            scope = "openid profile email offline_access urn:zitadel:iam:org:projects:roles"
            console.print(f"  -d 'scope={scope}'")
        else:
            # Show Device Flow step 1
            console.print("# Device Flow - Step 1: Get device code")
            console.print("curl -s -X POST \\")
            console.print(f"  '{settings.zitadel_issuer}/oauth/v2/device_authorization' \\")
            console.print(f"  -d 'client_id={settings.zitadel_client_id}' \\")
            scope = "openid profile email offline_access urn:zitadel:iam:org:projects:roles"
            console.print(f"  -d 'scope={scope}'")
            console.print()
            console.print("# Then visit verification_uri with user_code")
            console.print("# Device Flow - Step 2: Poll for token")
            console.print("curl -s -X POST \\")
            console.print(f"  '{settings.zitadel_issuer}/oauth/v2/token' \\")
            console.print("  -d 'grant_type=urn:ietf:params:oauth:grant-type:device_code' \\")
            console.print(f"  -d 'client_id={settings.zitadel_client_id}' \\")
            console.print("  -d 'device_code=DEVICE_CODE_FROM_STEP_1'")
        return

    import time

    try:
        if token:
            # Use Personal Access Token directly
            console.print("[dim]Using Personal Access Token...[/dim]")
            token_info = TokenInfo(
                access_token=token,
                refresh_token=None,
                expires_at=time.time() + 86400 * 365,  # Assume 1 year validity
                token_type="Bearer",
            )
            store_token(token_info)
            console.print("[green]Successfully logged in with PAT![/green]")
            console.print()
            # Auto-configure environment and project
            asyncio.run(auto_configure_after_login(token))
            return

        if email and password:
            # Use password-based authentication (ROPC)
            console.print(f"[dim]Logging in as {email}...[/dim]")
            token_info = asyncio.run(password_login(email, password))
        else:
            # Use Device Flow (interactive)
            token_info = asyncio.run(device_flow_login())

        store_token(token_info)
        console.print("[green]Successfully logged in![/green]")
        console.print()
        # Auto-configure project (environment already selected via prompt)
        asyncio.run(auto_configure_after_login(token_info.access_token, skip_env_detection=True))
    except AuthError as e:
        console.print(f"[red]Login failed:[/red] {e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Login cancelled.[/yellow]")
        raise SystemExit(1)


@click.command()
def logout():
    """Logout and clear stored credentials."""
    clear_token()
    console.print("[green]Logged out successfully.[/green]")


@click.command()
def status():
    """Show current authentication status."""
    from iflow.config import get_settings

    token = get_stored_token()

    if not token:
        console.print("[yellow]Not logged in.[/yellow]")
        console.print("Run [bold]iflow login[/bold] to authenticate.")
        return

    if is_token_expired(token):
        console.print("[yellow]Token expired.[/yellow]")
        console.print("Run [bold]iflow login[/bold] to re-authenticate.")
        return

    console.print("[green]Logged in.[/green]")

    # Show environment
    settings = get_settings()
    env_name = ENVIRONMENTS.get(settings.environment, {}).get("name", settings.environment)
    console.print(f"Environment: [cyan]{env_name}[/cyan]")

    # Try to decode token to show user info
    try:
        import base64
        import json

        # Decode JWT payload (middle part)
        payload_b64 = token.access_token.split(".")[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        if "email" in payload:
            console.print(f"User: [cyan]{payload['email']}[/cyan]")
        elif "sub" in payload:
            console.print(f"Subject: [cyan]{payload['sub']}[/cyan]")

    except Exception:
        pass  # Don't fail if we can't decode token

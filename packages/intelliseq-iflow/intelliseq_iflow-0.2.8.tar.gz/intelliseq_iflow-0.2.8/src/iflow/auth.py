"""OAuth Device Flow authentication for iseq-flow CLI."""

import asyncio
import json
import time
import webbrowser
from dataclasses import dataclass

import httpx
import keyring
from rich.console import Console

from iflow.config import get_settings

console = Console()


def _configure_keyring_fallback():
    """Configure fallback keyring backend if system keyring unavailable."""
    from keyring.backends.fail import Keyring as FailKeyring

    current_backend = keyring.get_keyring()

    # If we got the fail backend, switch to file-based storage
    if isinstance(current_backend, FailKeyring):
        try:
            from keyrings.alt.file import PlaintextKeyring

            # Use plaintext file backend as fallback
            # Stored in ~/.local/share/python_keyring/keyring_pass.cfg
            keyring.set_keyring(PlaintextKeyring())
        except ImportError:
            pass  # keyrings.alt not installed, will fail on keyring access


# Configure fallback on module load
_configure_keyring_fallback()


@dataclass
class TokenInfo:
    """OAuth token information."""

    access_token: str
    refresh_token: str | None
    expires_at: float  # Unix timestamp
    token_type: str = "Bearer"


class AuthError(Exception):
    """Authentication error."""

    pass


def get_stored_token() -> TokenInfo | None:
    """Get stored token from keyring."""
    settings = get_settings()
    token_json = keyring.get_password(settings.keyring_service, "token")
    if not token_json:
        return None

    try:
        data = json.loads(token_json)
        return TokenInfo(**data)
    except (json.JSONDecodeError, TypeError):
        return None


def store_token(token: TokenInfo) -> None:
    """Store token in keyring."""
    settings = get_settings()
    token_json = json.dumps({
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
        "expires_at": token.expires_at,
        "token_type": token.token_type,
    })
    keyring.set_password(settings.keyring_service, "token", token_json)


def clear_token() -> None:
    """Clear stored token from keyring."""
    settings = get_settings()
    try:
        keyring.delete_password(settings.keyring_service, "token")
    except keyring.errors.PasswordDeleteError:
        pass  # Token doesn't exist


def is_token_expired(token: TokenInfo) -> bool:
    """Check if token is expired (with 60s buffer)."""
    return time.time() > (token.expires_at - 60)


async def refresh_access_token(refresh_token: str) -> TokenInfo:
    """Refresh access token using refresh token."""
    settings = get_settings()
    token_url = f"{settings.zitadel_issuer}/oauth/v2/token"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": settings.zitadel_client_id,
                "refresh_token": refresh_token,
            },
        )

        if response.status_code != 200:
            raise AuthError(f"Failed to refresh token: {response.text}")

        data = response.json()
        return TokenInfo(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_at=time.time() + data.get("expires_in", 3600),
            token_type=data.get("token_type", "Bearer"),
        )


async def get_valid_token() -> str | None:
    """Get a valid access token, refreshing if needed."""
    token = get_stored_token()
    if not token:
        return None

    if is_token_expired(token):
        if token.refresh_token:
            try:
                token = await refresh_access_token(token.refresh_token)
                store_token(token)
            except AuthError:
                clear_token()
                return None
        else:
            clear_token()
            return None

    return token.access_token


async def password_login(email: str, password: str) -> TokenInfo:
    """
    Login with email and password using ROPC grant.

    This is for headless/CI environments where Device Flow isn't practical.
    Requires ROPC grant type to be enabled in Zitadel project settings.
    """
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        # Use ROPC (Resource Owner Password Credentials) grant
        response = await client.post(
            f"{settings.zitadel_issuer}/oauth/v2/token",
            data={
                "grant_type": "password",
                "client_id": settings.zitadel_client_id,
                "username": email,
                "password": password,
                "scope": "openid profile email offline_access urn:zitadel:iam:org:projects:roles",
            },
        )

        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_desc = error_data.get("error_description", response.text)
            raise AuthError(f"Login failed: {error_desc}")

        data = response.json()
        return TokenInfo(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=time.time() + data.get("expires_in", 3600),
            token_type=data.get("token_type", "Bearer"),
        )


async def device_flow_login() -> TokenInfo:
    """
    Perform OAuth Device Flow login.

    1. Request device code from Zitadel
    2. Display user code and verification URL
    3. Poll for token until user completes auth
    """
    settings = get_settings()

    # Step 1: Request device code
    device_auth_url = f"{settings.zitadel_issuer}/oauth/v2/device_authorization"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            device_auth_url,
            data={
                "client_id": settings.zitadel_client_id,
                "scope": "openid profile email offline_access urn:zitadel:iam:org:projects:roles",
            },
        )

        if response.status_code != 200:
            raise AuthError(f"Failed to start device flow: {response.text}")

        device_data = response.json()

    device_code = device_data["device_code"]
    user_code = device_data["user_code"]
    verification_uri = device_data["verification_uri"]
    verification_uri_complete = device_data.get("verification_uri_complete", verification_uri)
    interval = device_data.get("interval", 5)
    expires_in = device_data.get("expires_in", 600)

    # Step 2: Display instructions to user
    console.print()
    console.print("[bold]To authenticate, visit:[/bold]")
    console.print(f"  [link={verification_uri_complete}]{verification_uri_complete}[/link]")
    console.print()
    console.print(f"[bold]And enter code:[/bold] [cyan]{user_code}[/cyan]")
    console.print()

    # Try to open browser
    try:
        webbrowser.open(verification_uri_complete)
        console.print("[dim]Browser opened automatically.[/dim]")
    except Exception:
        console.print("[dim]Please open the URL manually.[/dim]")

    console.print()
    console.print("[dim]Waiting for authentication...[/dim]")

    # Step 3: Poll for token
    token_url = f"{settings.zitadel_issuer}/oauth/v2/token"
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        while time.time() - start_time < expires_in:
            await asyncio.sleep(interval)

            response = await client.post(
                token_url,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": settings.zitadel_client_id,
                    "device_code": device_code,
                },
            )

            if response.status_code == 200:
                data = response.json()
                return TokenInfo(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    expires_at=time.time() + data.get("expires_in", 3600),
                    token_type=data.get("token_type", "Bearer"),
                )

            error_data = response.json()
            error = error_data.get("error")

            if error == "authorization_pending":
                # User hasn't completed auth yet, keep polling
                continue
            elif error == "slow_down":
                # Increase interval
                interval += 5
                continue
            elif error == "expired_token":
                raise AuthError("Device code expired. Please try again.")
            elif error == "access_denied":
                raise AuthError("Access denied by user.")
            else:
                error_desc = error_data.get('error_description', error)
                raise AuthError(f"Authentication failed: {error_desc}")

    raise AuthError("Authentication timed out. Please try again.")

"""
Authentication commands for XSource CLI.
"""

import typer
from typing import Optional
from rich.prompt import Prompt, Confirm

from .config import get_credentials, Credentials
from .api import XSourceAPI, APIError
from .utils import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_user_info,
    Spinner,
    print_banner,
)

app = typer.Typer(help="Authentication commands")


@app.command("login")
def login(
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email address"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password (not recommended, use interactive)"),
):
    """
    Login to XSource Security.

    Interactive login is recommended for security.
    """
    print_banner()

    # Get email
    if not email:
        email = Prompt.ask("[bold cyan]Email[/bold cyan]")

    # Get password (hidden)
    if not password:
        password = Prompt.ask("[bold cyan]Password[/bold cyan]", password=True)

    if not email or not password:
        print_error("Email and password are required")
        raise typer.Exit(1)

    with Spinner("Authenticating...") as spinner:
        try:
            # Create API client without credentials
            api = XSourceAPI(credentials=Credentials())

            # Login
            result = api.login(email, password)

            # Save credentials
            creds = Credentials(
                access_token=result.get("access_token"),
                refresh_token=result.get("refresh_token"),
                email=email,
            )
            creds.save()

            spinner.update("Fetching user info...")

            # Get user info
            api_with_creds = XSourceAPI(credentials=creds)
            user_data = api_with_creds.get_me()

        except APIError as e:
            print_error(f"Login failed: {e.message}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Login failed: {e}")
            raise typer.Exit(1)

    console.print()
    print_success("Successfully logged in!")
    console.print()

    user = user_data.get("user", {})
    org = user_data.get("organization")
    print_user_info(user, org)


@app.command("logout")
def logout(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Logout and clear stored credentials.
    """
    if not force:
        if not Confirm.ask("Are you sure you want to logout?"):
            print_info("Cancelled")
            raise typer.Exit(0)

    creds = get_credentials()
    creds.clear()
    print_success("Successfully logged out")


@app.command("set-key")
def set_key(
    api_key: str = typer.Argument(..., help="Your XSource API key"),
):
    """
    Set API key for authentication.

    API keys can be generated from the XSource dashboard.
    """
    if not api_key.strip():
        print_error("API key cannot be empty")
        raise typer.Exit(1)

    with Spinner("Validating API key...") as spinner:
        try:
            # Validate the API key
            creds = Credentials(api_key=api_key.strip())
            api = XSourceAPI(credentials=creds)
            user_data = api.get_me()

            # Save credentials
            creds.save()

        except APIError as e:
            print_error(f"Invalid API key: {e.message}")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to validate API key: {e}")
            raise typer.Exit(1)

    console.print()
    print_success("API key saved successfully!")
    console.print()

    user = user_data.get("user", {})
    org = user_data.get("organization")
    print_user_info(user, org)


@app.command("whoami")
def whoami():
    """
    Show current authenticated user.
    """
    creds = get_credentials()

    if not creds.is_authenticated:
        print_warning("Not authenticated")
        print_info("Run [cyan]xsource login[/cyan] or [cyan]xsource auth set-key <key>[/cyan] to authenticate")
        raise typer.Exit(1)

    with Spinner("Fetching user info..."):
        try:
            api = XSourceAPI(credentials=creds)
            user_data = api.get_me()
        except APIError as e:
            print_error(f"Failed to get user info: {e.message}")
            print_info("Your session may have expired. Try logging in again.")
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to get user info: {e}")
            raise typer.Exit(1)

    console.print()
    user = user_data.get("user", {})
    org = user_data.get("organization")
    print_user_info(user, org)


@app.command("status")
def status():
    """
    Check authentication status.
    """
    creds = get_credentials()

    if creds.is_authenticated:
        if creds.email:
            print_success(f"Authenticated as [cyan]{creds.email}[/cyan]")
        elif creds.api_key:
            print_success("Authenticated with API key")
        else:
            print_success("Authenticated")

        # Try to fetch user info
        try:
            api = XSourceAPI(credentials=creds)
            user_data = api.get_me()
            org = user_data.get("organization", {})
            if org:
                console.print(f"  Organization: [bold]{org.get('name', '-')}[/bold]")
                console.print(f"  Plan: {org.get('plan', 'free').capitalize()}")
        except Exception:
            pass
    else:
        print_warning("Not authenticated")
        print_info("Run [cyan]xsource login[/cyan] to authenticate")

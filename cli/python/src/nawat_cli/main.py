"""Entry point for the nawat CLI."""

import json
from urllib.parse import urlsplit

import click
import requests

from nawat_cli import __version__
from nawat_cli.auth import clear_token, load_refresh_token, load_token, save_token

DEFAULT_BASE_URL = "https://roaming.bssconnects.io"


@click.group()
@click.version_option(__version__, prog_name="nawat")
def cli() -> None:
    """Nawat command-line interface."""


@cli.command()
@click.argument("url")
def ping(url: str) -> None:
    """Send a GET request to URL and print the status code."""
    response = requests.get(url, timeout=10)
    click.echo(f"{url} -> {response.status_code}")


@cli.group()
@click.option("--base-url", default=DEFAULT_BASE_URL, envvar="NAWAT_BASE_URL", show_default=True)
@click.pass_context
def auth(context: click.Context, base_url: str) -> None:
    """Manage platform authentication."""
    context.obj = base_url


def validate_base_url(base_url: str) -> None:
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc or parsed_url.username or parsed_url.password or parsed_url.path not in ("", "/") or parsed_url.query or parsed_url.fragment:
        raise click.ClickException("Authentication base URL must be an HTTPS origin")


def auth_request(base_url: str, method: str, endpoint: str, token: str | None = None, body: dict | None = None) -> requests.Response:
    validate_base_url(base_url)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    try:
        response = requests.request(method, f"{base_url.rstrip('/')}/api/v1/auth/{endpoint}",
                                    json=body, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        raise click.ClickException(f"Authentication request failed: {error}") from error
    return response


def response_data(response: requests.Response) -> dict:
    try:
        data = response.json()
    except ValueError as error:
        raise click.ClickException("Invalid authentication response") from error
    if not isinstance(data, dict):
        raise click.ClickException("Invalid authentication response")
    return data


def required_token(value: str | None, name: str = "access") -> str:
    if not value:
        raise click.ClickException(f"No {name} token configured; run 'nawat auth login' first")
    return value


@auth.command()
@click.option("--email", prompt=True)
@click.pass_obj
def login(base_url: str, email: str) -> None:
    """Log in with an email and password."""
    password = click.prompt("Password", hide_input=True)
    data = response_data(auth_request(base_url, "POST", "login", body={"email": email, "password": password}))
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    if not isinstance(access_token, str) or not access_token or not isinstance(refresh_token, str) or not refresh_token:
        raise click.ClickException("Login response did not include access and refresh tokens")
    save_token(access_token, refresh_token)
    click.echo("Logged in; tokens saved to ~/.nawat/config")


@auth.command()
@click.pass_obj
def refresh(base_url: str) -> None:
    """Refresh the stored access token."""
    try:
        refresh_token = required_token(load_refresh_token(), "refresh")
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    data = response_data(auth_request(base_url, "POST", "refresh", body={"refresh_token": refresh_token}))
    access_token = data.get("access_token")
    new_refresh_token = data.get("refresh_token", refresh_token)
    if not isinstance(access_token, str) or not access_token or not isinstance(new_refresh_token, str) or not new_refresh_token:
        raise click.ClickException("Refresh response did not include a valid token")
    save_token(access_token, new_refresh_token)
    click.echo("Access token refreshed")


@auth.command()
@click.pass_obj
def logout(base_url: str) -> None:
    """Log out and remove stored tokens."""
    try:
        token = required_token(load_token())
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    auth_request(base_url, "POST", "logout", token=token)
    clear_token()
    click.echo("Logged out")


@auth.command("me")
@click.pass_obj
def profile(base_url: str) -> None:
    """Show the current user profile."""
    try:
        token = required_token(load_token())
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    data = response_data(auth_request(base_url, "GET", "me", token=token))
    click.echo(json.dumps(data, indent=2))


@auth.command("change-password")
@click.pass_obj
def change_password(base_url: str) -> None:
    """Change the current user's password."""
    try:
        token = required_token(load_token())
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    current_password = click.prompt("Current password", hide_input=True)
    new_password = click.prompt("New password", hide_input=True, confirmation_prompt=True)
    auth_request(base_url, "POST", "change-password", token=token,
                 body={"current_password": current_password, "new_password": new_password})
    click.echo("Password changed")


@auth.command("set-token")
def set_token() -> None:
    """Store an access token from the platform."""
    token = click.prompt("Access token", hide_input=True)
    try:
        save_token(token)
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    click.echo("Token saved to ~/.nawat/config")


@auth.command()
def status() -> None:
    """Check whether an access token is stored."""
    try:
        token = load_token()
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    click.echo("Token configured" if token else "No token configured")


@cli.group()
@click.option("--base-url", default=DEFAULT_BASE_URL, envvar="NAWAT_BASE_URL", show_default=True)
@click.pass_context
def users(context: click.Context, base_url: str) -> None:
    """Manage platform users."""
    context.obj = base_url


@users.command("list")
@click.option("--search", default="", help="Filter by search text.")
@click.option("--role", default="", help="Filter by role.")
@click.option("--status", default="", help="Filter by status.")
@click.option("--page", type=click.IntRange(min=1), default=1, show_default=True)
@click.option("--page-size", type=click.IntRange(min=1), default=20, show_default=True)
@click.pass_obj
def list_users(base_url: str, search: str, role: str, status: str, page: int, page_size: int) -> None:
    """List users as a username and email table."""
    try:
        token = required_token(load_token())
    except ValueError as error:
        raise click.ClickException(str(error)) from error
    validate_base_url(base_url)
    params = {"search": search, "role": role, "status": status, "page": page, "page_size": page_size}
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/v1/admin/users", params=params,
                                headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        raise click.ClickException(f"Unable to list users: {error}") from error
    if "application/json" not in response.headers.get("Content-Type", ""):
        raise click.ClickException(f"Users endpoint returned {response.headers.get('Content-Type', 'no content type')} instead of JSON")
    try:
        payload = response.json()
    except ValueError as error:
        raise click.ClickException("Invalid users response") from error

    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = payload.get("users", payload.get("data"))
    else:
        entries = None
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        raise click.ClickException("Invalid users response")
    rows = [(str(entry.get("username") or "-").replace("\n", " ").replace("\r", " "),
             str(entry.get("email") or "-").replace("\n", " ").replace("\r", " ")) for entry in entries]
    width = max([len("USERNAME"), *(len(username) for username, _ in rows)])
    click.echo(f"{'USERNAME':<{width}}  EMAIL")
    for username, email in rows:
        click.echo(f"{username:<{width}}  {email}")


@cli.group()
def create() -> None:
    """Create Nawat resources."""

@create.command()
@click.option("--name", required=True, help="Name of the model to create.")
@click.option("--version", required=True, help="version of the model to create.")
def model(name: str,version:str) -> None:
    """Create a model with the given name."""
    click.echo(f"Creating model: {name} with {version}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()

"""
Command-line interface for httpgo using Typer.
https://typer.fastapi.org.cn/
"""

import json
import sys
import urllib.parse
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from . import __version__
from .parser import parse_http_file
from .client import HttpClient
from .variables import VariableManager
from .formatter import create_formatter
from .models import HttpRequest, AuthConfig, AuthType
from .config import config_manager, get_config


# Create the main app
app = typer.Typer(
    name="httpgo",
    help="httpgo - A powerful HTTP CLI that supports .http files.",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]httpgo[/bold cyan] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version", "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """
    [bold cyan]httpgo[/bold cyan] - A powerful HTTP CLI that supports .http files.

    Execute HTTP requests from .http files or directly from command line.

    [dim]Examples:[/dim]
        httpgo run api.http                    [dim]# Run all requests in file[/dim]
        httpgo run api.http --name "Get User"  [dim]# Run specific request[/dim]
        httpgo get https://httpbin.org/get     [dim]# Direct GET request[/dim]
        httpgo post https://httpbin.org/post name=value
    """
    pass


@app.command()
def run(
    file: Annotated[
        Path,
        typer.Argument(
            help="Path to .http file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    name: Annotated[
        Optional[str],
        typer.Option("--name", "-n", help="Run only the request with this name."),
    ] = None,
    index: Annotated[
        Optional[int],
        typer.Option("--index", "-i", help="Run only the request at this index (0-based)."),
    ] = None,
    run_all: Annotated[
        bool,
        typer.Option("--all", "-a", help="Run all requests in sequence."),
    ] = False,
    env: Annotated[
        Optional[Path],
        typer.Option("--env", "-e", help="Path to .env file for variables."),
    ] = None,
    var: Annotated[
        Optional[list[str]],
        typer.Option("--var", "-v", help="Set variable: name=value"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Show request details."),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Only show response body."),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable colored output."),
    ] = False,
    headers_only: Annotated[
        bool,
        typer.Option("--headers", "-h", help="Show only headers."),
    ] = False,
    body_only: Annotated[
        bool,
        typer.Option("--body", "-b", help="Show only body."),
    ] = False,
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Request timeout in seconds."),
    ] = 30.0,
    insecure: Annotated[
        bool,
        typer.Option("--insecure", "-k", help="Disable SSL verification."),
    ] = False,
    list_only: Annotated[
        bool,
        typer.Option("--list", "-l", help="List all requests without running."),
    ] = False,
    proxy: Annotated[
        Optional[str],
        typer.Option("--proxy", "-x", help="HTTP proxy URL (e.g., http://127.0.0.1:7890)."),
    ] = None,
) -> None:
    """
    Run requests from a .http file.

    [dim]Examples:[/dim]
        httpgo run api.http                     [dim]# Run first request[/dim]
        httpgo run api.http --list              [dim]# List all requests[/dim]
        httpgo run api.http --all               [dim]# Run all requests[/dim]
        httpgo run api.http -n "Create User"    [dim]# Run by name[/dim]
        httpgo run api.http -i 2                [dim]# Run third request[/dim]
        httpgo run api.http -v baseUrl=http://localhost:3000
        httpgo run api.http --proxy http://127.0.0.1:7890
    """
    # Setup variable manager
    variable_manager = VariableManager()

    if env:
        variable_manager.load_env_file(env)

    # Parse command-line variables
    if var:
        for v in var:
            if "=" in v:
                k, val = v.split("=", 1)
                variable_manager.set(k, val)

    # Parse the .http file
    try:
        http_file = parse_http_file(file, variable_manager)
    except Exception as e:
        console.print(f"[red]Error parsing file:[/red] {e}")
        raise typer.Exit(1)

    if not http_file.requests:
        console.print("[yellow]No requests found in file.[/yellow]")
        raise typer.Exit(0)

    # If --list flag, show requests and exit
    if list_only:
        _print_request_list(file, http_file.requests)
        raise typer.Exit(0)

    # Determine which requests to run
    requests_to_run: list[HttpRequest] = []

    if name:
        # Find by name
        for req in http_file.requests:
            if req.name and name.lower() in req.name.lower():
                requests_to_run.append(req)
                break
        if not requests_to_run:
            console.print(f"[red]No request found with name containing '[/red]{name}[red]'[/red]")
            raise typer.Exit(1)
    elif index is not None:
        if 0 <= index < len(http_file.requests):
            requests_to_run.append(http_file.requests[index])
        else:
            console.print(f"[red]Invalid index {index}. File has {len(http_file.requests)} requests.[/red]")
            raise typer.Exit(1)
    elif run_all:
        requests_to_run = http_file.requests
    else:
        # Run first request by default
        requests_to_run.append(http_file.requests[0])

    # Setup formatter
    formatter = create_formatter(
        verbose=verbose,
        quiet=quiet,
        headers=headers_only or (not body_only),
        body=body_only or (not headers_only),
        color=not no_color,
    )

    # Get config and apply overrides
    cfg = get_config()
    effective_proxy = proxy or cfg.proxy
    effective_timeout = timeout  # CLI always overrides
    effective_verify_ssl = not insecure if insecure else cfg.verify_ssl
    
    # Execute requests
    with HttpClient(
        timeout=effective_timeout,
        verify_ssl=effective_verify_ssl,
        proxy=effective_proxy,
    ) as client:
        for i, request in enumerate(requests_to_run):
            if len(requests_to_run) > 1:
                request_label = request.name or f"Request {i + 1}"
                console.print(f"\n[bold cyan]>>> {request_label}[/bold cyan]")

            if verbose:
                formatter.format_request(request)

            try:
                response = client.execute(request)
                formatter.format_response(response)
            except Exception as e:
                formatter.format_error(e)
                if not run_all:
                    raise typer.Exit(1)


def _print_request_list(file: Path, requests: list[HttpRequest]) -> None:
    """Print a formatted list of requests."""
    console.print(f"\n[bold]Requests in {file}:[/bold]\n")

    method_colors = {
        "GET": "green",
        "POST": "yellow",
        "PUT": "blue",
        "DELETE": "red",
        "PATCH": "magenta",
    }

    for i, req in enumerate(requests):
        method_color = method_colors.get(req.method, "white")
        url_display = req.url[:60] + ("..." if len(req.url) > 60 else "")

        console.print(f"  [{i}] [{method_color}]{req.method:7}[/{method_color}] {url_display}")
        if req.name:
            console.print(f"      [dim]Name: {req.name}[/dim]")

    console.print()


@app.command("list")
def list_requests(
    file: Annotated[
        Path,
        typer.Argument(
            help="Path to .http file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """List all requests in a .http file."""
    try:
        http_file = parse_http_file(file)
    except Exception as e:
        console.print(f"[red]Error parsing file:[/red] {e}")
        raise typer.Exit(1)

    if not http_file.requests:
        console.print("[yellow]No requests found in file.[/yellow]")
        return

    _print_request_list(file, http_file.requests)


# Auth type enum for CLI
class AuthTypeChoice(str, Enum):
    basic = "basic"
    bearer = "bearer"


def _execute_http_request(
    method: str,
    url: str,
    items: list[str],
    form: bool,
    header: list[str],
    auth: Optional[str],
    auth_type: AuthTypeChoice,
    verbose: bool,
    quiet: bool,
    no_color: bool,
    timeout: float,
    insecure: bool,
    proxy: Optional[str] = None,
) -> None:
    """Common logic for executing HTTP requests."""
    # Parse headers
    headers: dict[str, str] = {}
    data: dict[str, str] = {}
    json_data: dict[str, any] = {}

    for h in header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()

    # Parse items
    final_url = url
    for item in items:
        if ":=" in item:
            # JSON value
            k, v = item.split(":=", 1)
            try:
                json_data[k] = json.loads(v)
            except json.JSONDecodeError:
                json_data[k] = v
        elif "==" in item:
            # Query param (append to URL)
            k, v = item.split("==", 1)
            sep = "&" if "?" in final_url else "?"
            final_url = f"{final_url}{sep}{k}={v}"
        elif "=" in item:
            # Data field
            k, v = item.split("=", 1)
            data[k] = v
        elif ":" in item:
            # Header
            k, v = item.split(":", 1)
            headers[k.strip()] = v.strip()

    # Build body
    body = None
    if form and data:
        body = urllib.parse.urlencode(data)
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif data or json_data:
        combined = {**data, **json_data}
        body = json.dumps(combined)
        headers.setdefault("Content-Type", "application/json")

    # Build auth config
    auth_config = None
    if auth:
        if auth_type == AuthTypeChoice.bearer:
            auth_config = AuthConfig(type=AuthType.BEARER, token=auth)
        else:
            if ":" in auth:
                user, pwd = auth.split(":", 1)
                auth_config = AuthConfig(type=AuthType.BASIC, username=user, password=pwd)
            else:
                auth_config = AuthConfig(type=AuthType.BASIC, username=auth, password="")

    # Create request
    request = HttpRequest(
        method=method,
        url=final_url,
        headers=headers,
        body=body,
        auth=auth_config,
        timeout=timeout,
    )

    # Setup formatter
    formatter = create_formatter(
        verbose=verbose,
        quiet=quiet,
        color=not no_color,
    )

    # Get config and apply overrides
    cfg = get_config()
    effective_proxy = proxy or cfg.proxy
    effective_verify_ssl = not insecure if insecure else cfg.verify_ssl
    
    # Execute
    with HttpClient(
        timeout=timeout,
        verify_ssl=effective_verify_ssl,
        proxy=effective_proxy,
    ) as client:
        if verbose:
            formatter.format_request(request)

        try:
            response = client.execute(request)
            formatter.format_response(response)
        except Exception as e:
            formatter.format_error(e)
            raise typer.Exit(1)


# HTTP method commands using Typer
@app.command()
def get(
    url: Annotated[str, typer.Argument(help="Target URL")],
    items: Annotated[Optional[list[str]], typer.Argument(help="Request items (key=value, key:=json, Header:Value)")] = None,
    form: Annotated[bool, typer.Option("--form", "-f", help="Send data as form.")] = False,
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute a GET request."""
    _execute_http_request(
        "GET", url, items or [], form, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


@app.command()
def post(
    url: Annotated[str, typer.Argument(help="Target URL")],
    items: Annotated[Optional[list[str]], typer.Argument(help="Request items (key=value, key:=json, Header:Value)")] = None,
    form: Annotated[bool, typer.Option("--form", "-f", help="Send data as form.")] = False,
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute a POST request."""
    _execute_http_request(
        "POST", url, items or [], form, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


@app.command()
def put(
    url: Annotated[str, typer.Argument(help="Target URL")],
    items: Annotated[Optional[list[str]], typer.Argument(help="Request items (key=value, key:=json, Header:Value)")] = None,
    form: Annotated[bool, typer.Option("--form", "-f", help="Send data as form.")] = False,
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute a PUT request."""
    _execute_http_request(
        "PUT", url, items or [], form, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


@app.command()
def delete(
    url: Annotated[str, typer.Argument(help="Target URL")],
    items: Annotated[Optional[list[str]], typer.Argument(help="Request items (key=value, key:=json, Header:Value)")] = None,
    form: Annotated[bool, typer.Option("--form", "-f", help="Send data as form.")] = False,
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute a DELETE request."""
    _execute_http_request(
        "DELETE", url, items or [], form, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


@app.command()
def patch(
    url: Annotated[str, typer.Argument(help="Target URL")],
    items: Annotated[Optional[list[str]], typer.Argument(help="Request items (key=value, key:=json, Header:Value)")] = None,
    form: Annotated[bool, typer.Option("--form", "-f", help="Send data as form.")] = False,
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute a PATCH request."""
    _execute_http_request(
        "PATCH", url, items or [], form, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


@app.command()
def head(
    url: Annotated[str, typer.Argument(help="Target URL")],
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute a HEAD request."""
    _execute_http_request(
        "HEAD", url, [], False, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


@app.command()
def options(
    url: Annotated[str, typer.Argument(help="Target URL")],
    header: Annotated[Optional[list[str]], typer.Option("--header", "-H", help='Add header: "Name: Value"')] = None,
    auth: Annotated[Optional[str], typer.Option("--auth", "-a", help="Authentication: user:pass or token")] = None,
    auth_type: Annotated[AuthTypeChoice, typer.Option("--auth-type", help="Authentication type.")] = AuthTypeChoice.basic,
    verbose: Annotated[bool, typer.Option("--verbose", help="Show request details.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Only show response body.")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colored output.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Request timeout.")] = 30.0,
    insecure: Annotated[bool, typer.Option("--insecure", "-k", help="Disable SSL verification.")] = False,
    proxy: Annotated[Optional[str], typer.Option("--proxy", "-x", help="HTTP proxy URL.")] = None,
) -> None:
    """Execute an OPTIONS request."""
    _execute_http_request(
        "OPTIONS", url, [], False, header or [], auth, auth_type,
        verbose, quiet, no_color, timeout, insecure, proxy
    )


# ============================================================================
# Config commands
# ============================================================================

config_app = typer.Typer(
    name="config",
    help="Manage httpgo configuration.",
)
app.add_typer(config_app, name="config")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Config key (e.g., proxy, timeout)")],
    value: Annotated[str, typer.Argument(help="Config value")],
    local: Annotated[
        bool,
        typer.Option("--local", "-l", help="Save to local ./httpgo.toml instead of global config."),
    ] = False,
) -> None:
    """Set a configuration value.
    
    [dim]Examples:[/dim]
        httpgo config set proxy http://127.0.0.1:7890
        httpgo config set timeout 60
        httpgo config set verify_ssl false
        httpgo config set proxy http://proxy:8080 --local
    """
    # Type conversion for known keys
    typed_value: str | float | bool = value
    if key == "timeout":
        try:
            typed_value = float(value)
        except ValueError:
            console.print(f"[red]Error:[/red] timeout must be a number")
            raise typer.Exit(1)
    elif key in ("verify_ssl", "color", "verbose", "follow_redirects"):
        typed_value = value.lower() in ("true", "1", "yes", "on")
    
    scope = "local" if local else "global"
    config_manager.set(key, typed_value, scope=scope)
    
    scope_label = "local" if local else "global"
    console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [yellow]{value}[/yellow] ({scope_label})")


@config_app.command("get")
def config_get(
    key: Annotated[str, typer.Argument(help="Config key to get")],
) -> None:
    """Get a configuration value.
    
    [dim]Examples:[/dim]
        httpgo config get proxy
        httpgo config get timeout
    """
    value = config_manager.get(key)
    if value is None:
        console.print(f"[dim]{key}[/dim] is not set")
    else:
        console.print(f"[cyan]{key}[/cyan] = [yellow]{value}[/yellow]")


@config_app.command("unset")
def config_unset(
    key: Annotated[str, typer.Argument(help="Config key to remove")],
    local: Annotated[
        bool,
        typer.Option("--local", "-l", help="Remove from local ./httpgo.toml."),
    ] = False,
) -> None:
    """Remove a configuration value.
    
    [dim]Examples:[/dim]
        httpgo config unset proxy
        httpgo config unset proxy --local
    """
    scope = "local" if local else "global"
    removed = config_manager.unset(key, scope=scope)
    
    if removed:
        console.print(f"[green]✓[/green] Removed [cyan]{key}[/cyan]")
    else:
        console.print(f"[yellow]Key [cyan]{key}[/cyan] was not set[/yellow]")


@config_app.command("list")
def config_list() -> None:
    """List all configuration values.
    
    [dim]Example:[/dim]
        httpgo config list
    """
    config = config_manager.list_all()
    
    if not config:
        console.print("[dim]No configuration set[/dim]")
        return
    
    console.print("\n[bold]Current Configuration:[/bold]\n")
    
    for key, value in sorted(config.items()):
        if value is None:
            console.print(f"  [cyan]{key}[/cyan] = [dim]not set[/dim]")
        else:
            console.print(f"  [cyan]{key}[/cyan] = [yellow]{value}[/yellow]")
    
    console.print()


@config_app.command("path")
def config_path() -> None:
    """Show configuration file paths.
    
    [dim]Example:[/dim]
        httpgo config path
    """
    console.print("\n[bold]Config File Locations:[/bold]\n")
    
    for path, exists in config_manager.get_config_files():
        status = "[green]✓[/green]" if exists else "[dim]○[/dim]"
        console.print(f"  {status} {path}")
    
    console.print()


if __name__ == "__main__":
    app()

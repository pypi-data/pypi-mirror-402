"""
Output formatter with httpie-style colorized output.
Uses Rich for beautiful terminal output.
"""

import json
from typing import Literal

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.style import Style

from .models import HttpRequest, HttpResponse


# Color scheme inspired by httpie
class Colors:
    """Color definitions for output."""
    # Status codes
    SUCCESS = "bold green"
    REDIRECT = "bold yellow"
    CLIENT_ERROR = "bold red"
    SERVER_ERROR = "bold red reverse"
    
    # Request
    METHOD = "bold cyan"
    URL = "white"
    
    # Headers
    HEADER_NAME = "cyan"
    HEADER_VALUE = "white"
    
    # Body
    JSON_KEY = "cyan"
    JSON_STRING = "green"
    JSON_NUMBER = "yellow"
    JSON_BOOL = "magenta"
    
    # Misc
    DIM = "dim"
    HIGHLIGHT = "bold yellow"


class OutputFormatter:
    """Formats HTTP requests and responses for terminal output."""
    
    def __init__(
        self,
        console: Console | None = None,
        style: Literal["httpie", "verbose", "minimal"] = "httpie",
        color: bool = True,
        show_headers: bool = True,
        show_body: bool = True,
    ):
        self.console = console or Console(force_terminal=color)
        self.style = style
        self.color = color
        self.show_headers = show_headers
        self.show_body = show_body
    
    def format_request(self, request: HttpRequest) -> None:
        """Format and print a request."""
        if self.style == "minimal":
            return
        
        # Request line
        method_text = Text(request.method, style=Colors.METHOD)
        url_text = Text(f" {request.url}", style=Colors.URL)
        
        self.console.print()
        self.console.print(method_text + url_text)
        
        # Headers
        if self.show_headers and request.headers:
            for name, value in request.headers.items():
                self._print_header(name, value)
        
        # Body
        if self.show_body and request.body:
            self.console.print()
            self._print_body(request.body, request.headers.get("Content-Type", ""))
    
    def format_response(self, response: HttpResponse, show_time: bool = True) -> None:
        """Format and print a response."""
        # Status line
        status_style = self._get_status_style(response.status_code)
        
        status_text = Text()
        status_text.append("HTTP ", style=Colors.DIM)
        status_text.append(f"{response.status_code} ", style=status_style)
        status_text.append(response.reason, style=status_style)
        
        if show_time:
            time_str = self._format_time(response.elapsed)
            size_str = self._format_size(response.size)
            status_text.append(f"  [{time_str}, {size_str}]", style=Colors.DIM)
        
        self.console.print()
        self.console.print(status_text)
        
        # Headers
        if self.show_headers:
            for name, value in response.headers.items():
                self._print_header(name, value)
        
        # Body
        if self.show_body and response.body:
            self.console.print()
            content_type = response.headers.get("content-type", "")
            self._print_body(response.body, content_type)
    
    def format_error(self, error: Exception) -> None:
        """Format and print an error."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold red]Error:[/bold red] {str(error)}",
                border_style="red",
                title="Request Failed",
            )
        )
    
    def _print_header(self, name: str, value: str) -> None:
        """Print a single header."""
        text = Text()
        text.append(name, style=Colors.HEADER_NAME)
        text.append(": ", style=Colors.DIM)
        text.append(value, style=Colors.HEADER_VALUE)
        self.console.print(text)
    
    def _print_body(self, body: str, content_type: str) -> None:
        """Print the body with appropriate formatting."""
        if "application/json" in content_type or self._looks_like_json(body):
            try:
                # Pretty-print JSON
                parsed = json.loads(body)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                syntax = Syntax(
                    formatted,
                    "json",
                    theme="monokai",
                    word_wrap=True,
                )
                self.console.print(syntax)
            except json.JSONDecodeError:
                self.console.print(body)
        elif "text/html" in content_type:
            syntax = Syntax(body, "html", theme="monokai", word_wrap=True)
            self.console.print(syntax)
        elif "text/xml" in content_type or "application/xml" in content_type:
            syntax = Syntax(body, "xml", theme="monokai", word_wrap=True)
            self.console.print(syntax)
        else:
            self.console.print(body)
    
    def _looks_like_json(self, body: str) -> bool:
        """Check if body looks like JSON."""
        stripped = body.strip()
        return (stripped.startswith('{') and stripped.endswith('}')) or \
               (stripped.startswith('[') and stripped.endswith(']'))
    
    def _get_status_style(self, status_code: int) -> str:
        """Get the style for a status code."""
        if 200 <= status_code < 300:
            return Colors.SUCCESS
        elif 300 <= status_code < 400:
            return Colors.REDIRECT
        elif 400 <= status_code < 500:
            return Colors.CLIENT_ERROR
        else:
            return Colors.SERVER_ERROR
    
    def _format_time(self, elapsed: float) -> str:
        """Format elapsed time."""
        if elapsed < 1:
            return f"{elapsed * 1000:.0f}ms"
        return f"{elapsed:.2f}s"
    
    def _format_size(self, size: int) -> str:
        """Format response size."""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size / 1024 / 1024:.1f}MB"


class QuietFormatter(OutputFormatter):
    """Minimal output formatter - only prints response body."""
    
    def __init__(self, console: Console | None = None):
        super().__init__(console, style="minimal", show_headers=False)
    
    def format_request(self, request: HttpRequest) -> None:
        pass
    
    def format_response(self, response: HttpResponse, show_time: bool = False) -> None:
        if response.body:
            content_type = response.headers.get("content-type", "")
            self._print_body(response.body, content_type)


class VerboseFormatter(OutputFormatter):
    """Verbose output formatter - shows everything including request."""
    
    def __init__(self, console: Console | None = None, color: bool = True):
        super().__init__(console, style="verbose", color=color)
    
    def format_request(self, request: HttpRequest) -> None:
        """Format request with full details."""
        self.console.print()
        self.console.rule("[bold]Request[/bold]", style="dim")
        super().format_request(request)
    
    def format_response(self, response: HttpResponse, show_time: bool = True) -> None:
        """Format response with full details."""
        self.console.print()
        self.console.rule("[bold]Response[/bold]", style="dim")
        super().format_response(response, show_time)


def create_formatter(
    verbose: bool = False,
    quiet: bool = False,
    headers: bool = True,
    body: bool = True,
    color: bool = True,
) -> OutputFormatter:
    """Create an appropriate formatter based on options."""
    if quiet:
        return QuietFormatter()
    if verbose:
        return VerboseFormatter(color=color)
    return OutputFormatter(
        show_headers=headers,
        show_body=body,
        color=color,
    )

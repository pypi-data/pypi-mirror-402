"""
Authentication handlers for HTTP requests.
Supports Basic, Bearer, API Key, and Digest authentication.
"""

import base64
import hashlib
import time
from typing import Protocol

import httpx

from .models import AuthConfig, AuthType


class AuthHandler(Protocol):
    """Protocol for authentication handlers."""
    
    def apply(self, request: httpx.Request) -> httpx.Request:
        """Apply authentication to a request."""
        ...


class BasicAuth:
    """HTTP Basic Authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        """Add Basic auth header."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {encoded}'
        return headers


class BearerAuth:
    """Bearer Token Authentication."""
    
    def __init__(self, token: str):
        self.token = token
    
    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        """Add Bearer token header."""
        headers['Authorization'] = f'Bearer {self.token}'
        return headers


class ApiKeyAuth:
    """API Key Authentication."""
    
    def __init__(self, api_key: str, name: str = "X-API-Key", location: str = "header"):
        self.api_key = api_key
        self.name = name
        self.location = location  # 'header' or 'query'
    
    def apply_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Add API key to headers."""
        if self.location == "header":
            headers[self.name] = self.api_key
        return headers
    
    def apply_query(self, url: str) -> str:
        """Add API key to query string."""
        if self.location == "query":
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}{self.name}={self.api_key}"
        return url


class DigestAuth:
    """HTTP Digest Authentication (basic implementation)."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def get_httpx_auth(self) -> httpx.DigestAuth:
        """Get httpx DigestAuth instance."""
        return httpx.DigestAuth(self.username, self.password)


def create_auth_handler(config: AuthConfig) -> BasicAuth | BearerAuth | ApiKeyAuth | DigestAuth | None:
    """Create an appropriate auth handler based on config."""
    if config.type == AuthType.NONE:
        return None
    
    if config.type == AuthType.BASIC:
        if config.username and config.password:
            return BasicAuth(config.username, config.password)
        elif config.token:
            # Token is already base64 encoded credentials
            try:
                decoded = base64.b64decode(config.token).decode()
                if ':' in decoded:
                    username, password = decoded.split(':', 1)
                    return BasicAuth(username, password)
            except Exception:
                pass
    
    if config.type == AuthType.BEARER:
        if config.token:
            return BearerAuth(config.token)
    
    if config.type == AuthType.API_KEY:
        if config.api_key:
            return ApiKeyAuth(
                config.api_key,
                config.api_key_name,
                config.api_key_in
            )
    
    if config.type == AuthType.DIGEST:
        if config.username and config.password:
            return DigestAuth(config.username, config.password)
    
    return None


def apply_auth_to_request(
    config: AuthConfig | None,
    headers: dict[str, str],
    url: str
) -> tuple[dict[str, str], str, httpx.Auth | None]:
    """Apply authentication to request parameters.
    
    Returns:
        Tuple of (updated_headers, updated_url, httpx_auth_or_none)
    """
    if config is None or config.type == AuthType.NONE:
        return headers, url, None
    
    handler = create_auth_handler(config)
    if handler is None:
        return headers, url, None
    
    httpx_auth = None
    
    if isinstance(handler, BasicAuth):
        headers = handler.apply(headers.copy())
    elif isinstance(handler, BearerAuth):
        headers = handler.apply(headers.copy())
    elif isinstance(handler, ApiKeyAuth):
        headers = handler.apply_headers(headers.copy())
        url = handler.apply_query(url)
    elif isinstance(handler, DigestAuth):
        httpx_auth = handler.get_httpx_auth()
    
    return headers, url, httpx_auth

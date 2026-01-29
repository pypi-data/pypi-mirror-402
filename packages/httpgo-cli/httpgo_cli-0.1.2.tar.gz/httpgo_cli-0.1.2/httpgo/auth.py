"""
Authentication handlers for HTTP requests.
Supports Basic, Bearer, API Key, Digest, and Ed25519 signature authentication.
"""

import base64
import hashlib
import time
from typing import Protocol
from urllib.parse import urlparse, urlencode, parse_qsl

import httpx
from nacl.signing import SigningKey

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


class Ed25519Auth:
    """Ed25519 Signature Authentication (Cobo API style).
    
    Signs requests using Ed25519 and adds the following headers:
    - Biz-Api-Key: The API key
    - Biz-Api-Nonce: Timestamp in milliseconds
    - Biz-Api-Signature: Ed25519 signature of the request
    
    Sign content format: method|path|nonce|queryString|body
    Then double SHA256 hash, then Ed25519 sign.
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
    
    def _construct_sign_content(self, method: str, url: str, body: str | None, nonce: str) -> str:
        """Construct the content to be signed.
        
        Format: method|path|nonce|queryString|body
        """
        parsed = urlparse(url)
        path = parsed.path
        
        # Ensure path starts with /v2 (Cobo API specific)
        if not path.startswith("/v2"):
            path = "/v2" + path
        
        # Process query string
        query_string = ""
        if parsed.query:
            params = parse_qsl(parsed.query, keep_blank_values=True)
            if params:
                query_string = "&".join(
                    f"{k}={v.replace(' ', '+')}" for k, v in params
                )
        
        body_str = body or ""
        
        # Construct the string to sign
        return f"{method}|{path}|{nonce}|{query_string}|{body_str}"
    
    def _double_sha256(self, content: str) -> str:
        """Apply double SHA256 hash, return hex string."""
        first_hash = hashlib.sha256(content.encode()).digest()
        return hashlib.sha256(first_hash).hexdigest()
    
    def _sign(self, message_hex: str) -> str:
        """Sign the message using Ed25519.
        
        Args:
            message_hex: The message as a hex string (will be converted to bytes)
        
        Returns:
            Signature as hex string
        """
        message_bytes = bytes.fromhex(message_hex)
        private_key_bytes = bytes.fromhex(self.api_secret)
        signing_key = SigningKey(private_key_bytes)
        signed = signing_key.sign(message_bytes)
        return signed.signature.hex()
    
    def apply(self, method: str, url: str, headers: dict[str, str], body: str | None) -> dict[str, str]:
        """Apply Ed25519 signature authentication to headers."""
        nonce = str(int(time.time() * 1000))
        
        # Construct and hash the content
        sign_content = self._construct_sign_content(method, url, body, nonce)
        hash_to_sign = self._double_sha256(sign_content)
        
        # Sign
        signature = self._sign(hash_to_sign)
        
        # Add headers
        headers = headers.copy()
        headers['Biz-Api-Key'] = self.api_key
        headers['Biz-Api-Nonce'] = nonce
        headers['Biz-Api-Signature'] = signature
        
        return headers


# Backward compatibility alias
CoboAuth = Ed25519Auth


def create_auth_handler(config: AuthConfig) -> BasicAuth | BearerAuth | ApiKeyAuth | DigestAuth | Ed25519Auth | None:
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
    
    if config.type == AuthType.ED25519:
        if config.api_key and config.api_secret:
            return Ed25519Auth(config.api_key, config.api_secret)
    
    return None


def apply_auth_to_request(
    config: AuthConfig | None,
    headers: dict[str, str],
    url: str,
    method: str = "GET",
    body: str | None = None,
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
    elif isinstance(handler, Ed25519Auth):
        headers = handler.apply(method, url, headers, body)
    
    return headers, url, httpx_auth

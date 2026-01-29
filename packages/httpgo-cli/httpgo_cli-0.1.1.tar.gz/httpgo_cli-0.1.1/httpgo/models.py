"""
Data models for HTTP requests and responses.
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class AuthType(Enum):
    """Supported authentication types."""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"
    DIGEST = "digest"


@dataclass
class AuthConfig:
    """Authentication configuration."""
    type: AuthType = AuthType.NONE
    username: str | None = None
    password: str | None = None
    token: str | None = None
    api_key: str | None = None
    api_key_name: str = "X-API-Key"
    api_key_in: str = "header"  # header or query


@dataclass
class HttpRequest:
    """Represents a single HTTP request."""
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: str | None = None
    name: str | None = None
    auth: AuthConfig | None = None
    timeout: float = 30.0
    
    def __post_init__(self):
        self.method = self.method.upper()


@dataclass
class HttpResponse:
    """Represents an HTTP response."""
    status_code: int
    reason: str
    headers: dict[str, str]
    body: str
    elapsed: float  # in seconds
    size: int  # response size in bytes
    
    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300
    
    @property
    def is_json(self) -> bool:
        content_type = self.headers.get("content-type", "")
        return "application/json" in content_type


@dataclass
class HttpFile:
    """Represents a parsed .http file."""
    requests: list[HttpRequest] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    file_path: str | None = None

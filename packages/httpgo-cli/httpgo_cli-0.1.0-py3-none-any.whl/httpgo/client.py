"""
HTTP client for executing requests.
"""

import time
from typing import Any

import httpx

from .models import HttpRequest, HttpResponse, AuthConfig
from .auth import apply_auth_to_request


class HttpClient:
    """HTTP client for executing requests."""
    
    def __init__(
        self,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        follow_redirects: bool = True,
        proxy: str | None = None,
    ):
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.follow_redirects = follow_redirects
        self.proxy = proxy
        self._client: httpx.Client | None = None
    
    def _get_client(self) -> httpx.Client:
        """Get or create the httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                verify=self.verify_ssl,
                follow_redirects=self.follow_redirects,
                proxy=self.proxy,
            )
        return self._client
    
    def execute(self, request: HttpRequest) -> HttpResponse:
        """Execute an HTTP request and return the response."""
        client = self._get_client()
        
        # Prepare headers
        headers = dict(request.headers)
        
        # Apply authentication
        url = request.url
        httpx_auth = None
        if request.auth:
            headers, url, httpx_auth = apply_auth_to_request(
                request.auth, headers, url
            )
        
        # Prepare request kwargs
        kwargs: dict[str, Any] = {
            "method": request.method,
            "url": url,
            "headers": headers,
        }
        
        # Add body if present
        if request.body:
            content_type = headers.get("Content-Type", headers.get("content-type", ""))
            
            if "application/json" in content_type:
                kwargs["content"] = request.body
            elif "application/x-www-form-urlencoded" in content_type:
                kwargs["content"] = request.body
            elif "multipart/form-data" in content_type:
                kwargs["content"] = request.body
            else:
                kwargs["content"] = request.body
        
        # Add auth if needed (for Digest auth)
        if httpx_auth:
            kwargs["auth"] = httpx_auth
        
        # Execute request
        start_time = time.perf_counter()
        response = client.request(**kwargs)
        elapsed = time.perf_counter() - start_time
        
        # Build response
        return HttpResponse(
            status_code=response.status_code,
            reason=response.reason_phrase or "",
            headers=dict(response.headers),
            body=response.text,
            elapsed=elapsed,
            size=len(response.content),
        )
    
    def close(self):
        """Close the client."""
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


async def execute_async(request: HttpRequest) -> HttpResponse:
    """Execute a request asynchronously."""
    async with httpx.AsyncClient(
        timeout=request.timeout,
        follow_redirects=True,
    ) as client:
        # Prepare headers
        headers = dict(request.headers)
        
        # Apply authentication
        url = request.url
        httpx_auth = None
        if request.auth:
            headers, url, httpx_auth = apply_auth_to_request(
                request.auth, headers, url
            )
        
        # Prepare request kwargs
        kwargs: dict[str, Any] = {
            "method": request.method,
            "url": url,
            "headers": headers,
        }
        
        if request.body:
            kwargs["content"] = request.body
        
        if httpx_auth:
            kwargs["auth"] = httpx_auth
        
        # Execute request
        start_time = time.perf_counter()
        response = await client.request(**kwargs)
        elapsed = time.perf_counter() - start_time
        
        return HttpResponse(
            status_code=response.status_code,
            reason=response.reason_phrase or "",
            headers=dict(response.headers),
            body=response.text,
            elapsed=elapsed,
            size=len(response.content),
        )

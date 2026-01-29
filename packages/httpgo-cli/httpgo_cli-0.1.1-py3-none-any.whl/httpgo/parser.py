"""
Parser for .http and .rest files.
Supports the VS Code REST Client format.
"""

import re
from pathlib import Path
from typing import Iterator

from .models import HttpRequest, HttpFile, AuthConfig, AuthType
from .variables import VariableManager


class HttpFileParser:
    """Parser for .http files."""
    
    # Request separator
    REQUEST_SEPARATOR = re.compile(r'^###\s*(.*)?$', re.MULTILINE)
    
    # Request line pattern: METHOD URL [HTTP/version]
    REQUEST_LINE = re.compile(r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE|CONNECT)\s+(\S+)(?:\s+HTTP/[\d.]+)?$', re.IGNORECASE)
    
    # Variable definition: @name = value
    VARIABLE_DEF = re.compile(r'^@(\w+)\s*=\s*(.+)$')
    
    # Header pattern: Name: Value
    HEADER_PATTERN = re.compile(r'^([A-Za-z0-9_-]+):\s*(.+)$')
    
    # Comment patterns
    COMMENT_PATTERNS = [
        re.compile(r'^#(?!##).*$'),   # # comment (but not ###)
        re.compile(r'^//.*$'),         # // comment
    ]
    
    def __init__(self, variable_manager: VariableManager | None = None):
        self.variables = variable_manager or VariableManager()
    
    def parse_file(self, path: str | Path) -> HttpFile:
        """Parse a .http file."""
        path = Path(path)
        with open(path, encoding='utf-8') as f:
            content = f.read()
        
        http_file = self.parse_content(content)
        http_file.file_path = str(path)
        
        # Try to load environment files from same directory
        env_path = path.parent / '.env'
        if env_path.exists():
            self.variables.load_env_file(env_path)
        
        http_client_env = path.parent / 'http-client.env.json'
        if http_client_env.exists():
            self.variables.load_http_client_env(http_client_env)
        
        return http_file
    
    def parse_content(self, content: str) -> HttpFile:
        """Parse .http file content."""
        http_file = HttpFile()
        
        # Split by request separator
        parts = self.REQUEST_SEPARATOR.split(content)
        
        # First part may contain global variables
        first_part = parts[0] if parts else ""
        file_vars = self._extract_variables(first_part)
        http_file.variables = file_vars
        self.variables.set_many(file_vars)
        
        # Process request blocks
        # parts[0] is before first ###, then alternating: name, content, name, content...
        i = 0
        while i < len(parts):
            if i == 0:
                # First block - might contain a request or just variables
                request = self._parse_request_block(parts[i])
                if request:
                    http_file.requests.append(request)
                i += 1
            else:
                # After separator: parts[i] is the request name, parts[i+1] is content
                request_name = parts[i].strip() if parts[i] else None
                i += 1
                if i < len(parts):
                    request = self._parse_request_block(parts[i], request_name)
                    if request:
                        http_file.requests.append(request)
                    i += 1
        
        return http_file
    
    def _extract_variables(self, content: str) -> dict[str, str]:
        """Extract variable definitions from content."""
        variables = {}
        for line in content.split('\n'):
            line = line.strip()
            match = self.VARIABLE_DEF.match(line)
            if match:
                name, value = match.groups()
                variables[name] = value.strip()
        return variables
    
    def _parse_request_block(self, content: str, name: str | None = None) -> HttpRequest | None:
        """Parse a single request block."""
        lines = content.split('\n')
        
        # Extract variables from this block
        block_vars = self._extract_variables(content)
        self.variables.set_many(block_vars)
        
        # Find the request line
        request_line_idx = None
        method = None
        url = None
        
        for idx, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines, comments, and variable definitions
            if not line or self._is_comment(line) or self.VARIABLE_DEF.match(line):
                continue
            
            match = self.REQUEST_LINE.match(line)
            if match:
                method = match.group(1).upper()
                url = match.group(2)
                request_line_idx = idx
                break
        
        if request_line_idx is None or not method or not url:
            return None
        
        # Parse headers (lines after request line until empty line or body)
        headers: dict[str, str] = {}
        body_start_idx = None
        
        for idx in range(request_line_idx + 1, len(lines)):
            line = lines[idx]
            stripped = line.strip()
            
            # Skip comments
            if self._is_comment(stripped):
                continue
            
            # Empty line marks start of body
            if not stripped:
                body_start_idx = idx + 1
                break
            
            # Try to parse as header
            header_match = self.HEADER_PATTERN.match(stripped)
            if header_match:
                header_name, header_value = header_match.groups()
                headers[header_name] = header_value.strip()
            else:
                # If not a header, might be start of body
                body_start_idx = idx
                break
        
        # Parse body
        body = None
        if body_start_idx is not None:
            body_lines = []
            for idx in range(body_start_idx, len(lines)):
                line = lines[idx]
                # Don't strip body lines - preserve formatting
                if not self._is_comment(line.strip()):
                    body_lines.append(line)
            
            body_text = '\n'.join(body_lines).strip()
            if body_text:
                body = body_text
        
        # Resolve variables in URL, headers, and body
        url = self.variables.resolve(url)
        headers = {k: self.variables.resolve(v) for k, v in headers.items()}
        if body:
            body = self.variables.resolve(body)
        
        # Extract auth from headers if present
        auth = self._extract_auth(headers)
        
        return HttpRequest(
            method=method,
            url=url,
            headers=headers,
            body=body,
            name=name,
            auth=auth,
        )
    
    def _is_comment(self, line: str) -> bool:
        """Check if a line is a comment."""
        for pattern in self.COMMENT_PATTERNS:
            if pattern.match(line):
                return True
        return False
    
    def _extract_auth(self, headers: dict[str, str]) -> AuthConfig | None:
        """Extract authentication config from headers."""
        auth_header = headers.get('Authorization', '')
        
        if auth_header.lower().startswith('basic '):
            # Basic auth - decode not needed, just pass through
            return AuthConfig(type=AuthType.BASIC, token=auth_header[6:])
        
        if auth_header.lower().startswith('bearer '):
            return AuthConfig(type=AuthType.BEARER, token=auth_header[7:])
        
        # Check for API key headers
        for key in ['X-API-Key', 'X-Api-Key', 'x-api-key', 'Api-Key', 'api-key']:
            if key in headers:
                return AuthConfig(
                    type=AuthType.API_KEY,
                    api_key=headers[key],
                    api_key_name=key,
                    api_key_in='header'
                )
        
        return None


def parse_http_file(path: str | Path, variable_manager: VariableManager | None = None) -> HttpFile:
    """Convenience function to parse a .http file."""
    parser = HttpFileParser(variable_manager)
    return parser.parse_file(path)

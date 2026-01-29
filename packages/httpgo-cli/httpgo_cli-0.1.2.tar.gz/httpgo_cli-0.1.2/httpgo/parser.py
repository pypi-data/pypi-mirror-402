"""
Parser for .http and .rest files.
Supports JetBrains HTTP Client / VS Code REST Client format.

Reference: https://www.jetbrains.com/help/idea/http-client-in-product-code-editor.html
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator
from enum import Enum

from .models import HttpRequest, HttpFile, AuthConfig, AuthType
from .variables import VariableManager


class TokenType(Enum):
    """Token types for lexical analysis."""
    SEPARATOR = "separator"          # ###
    REQUEST_LINE = "request_line"    # GET /path HTTP/1.1
    HEADER = "header"                # Name: Value
    BODY_LINE = "body_line"          # Body content
    VARIABLE_DEF = "variable_def"    # @name = value
    COMMENT = "comment"              # # comment or // comment
    DIRECTIVE = "directive"          # # @name: value
    EMPTY = "empty"                  # Empty line
    PRE_REQUEST = "pre_request"      # < {% script %}
    RESPONSE_HANDLER = "response"    # > {% script %}


@dataclass
class Token:
    """A lexical token."""
    type: TokenType
    value: str
    line_number: int
    raw: str = ""
    
    # For specific token types
    directive_name: str | None = None
    directive_value: str | None = None
    header_name: str | None = None
    header_value: str | None = None
    method: str | None = None
    url: str | None = None
    var_name: str | None = None
    var_value: str | None = None


class HttpLexer:
    """Lexical analyzer for .http files."""
    
    # Patterns
    SEPARATOR = re.compile(r'^###\s*(.*)$')
    REQUEST_LINE = re.compile(
        r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE|CONNECT)\s+(\S+)(?:\s+HTTP/[\d.]+)?$',
        re.IGNORECASE
    )
    VARIABLE_DEF = re.compile(r'^@(\w[\w_]*)\s*=\s*(.+)$')
    HEADER = re.compile(r'^([A-Za-z0-9_-]+):\s*(.*)$')
    DIRECTIVE = re.compile(r'^#\s*@(\w+):\s*(.*)$', re.IGNORECASE)
    COMMENT_HASH = re.compile(r'^#(?!##)(?!\s*@).*$')
    COMMENT_SLASH = re.compile(r'^//.*$')
    PRE_REQUEST_START = re.compile(r'^<\s*\{%')
    RESPONSE_HANDLER_START = re.compile(r'^>\s*\{%')
    
    def tokenize(self, content: str) -> list[Token]:
        """Tokenize the content into a list of tokens."""
        tokens: list[Token] = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            line_num = i + 1
            
            # Empty line
            if not stripped:
                tokens.append(Token(TokenType.EMPTY, "", line_num, line))
                i += 1
                continue
            
            # Request separator: ###
            match = self.SEPARATOR.match(stripped)
            if match:
                tokens.append(Token(
                    TokenType.SEPARATOR, 
                    match.group(1).strip() or "",
                    line_num, line
                ))
                i += 1
                continue
            
            # Variable definition: @name = value
            match = self.VARIABLE_DEF.match(stripped)
            if match:
                tokens.append(Token(
                    TokenType.VARIABLE_DEF,
                    stripped, line_num, line,
                    var_name=match.group(1),
                    var_value=match.group(2).strip()
                ))
                i += 1
                continue
            
            # Directive: # @name: value
            match = self.DIRECTIVE.match(stripped)
            if match:
                tokens.append(Token(
                    TokenType.DIRECTIVE,
                    stripped, line_num, line,
                    directive_name=match.group(1).lower(),
                    directive_value=match.group(2).strip()
                ))
                i += 1
                continue
            
            # Comment: # or //
            if self.COMMENT_HASH.match(stripped) or self.COMMENT_SLASH.match(stripped):
                tokens.append(Token(TokenType.COMMENT, stripped, line_num, line))
                i += 1
                continue
            
            # Pre-request script: < {% ... %}
            if self.PRE_REQUEST_START.match(stripped):
                script, end_idx = self._extract_script(lines, i)
                tokens.append(Token(TokenType.PRE_REQUEST, script, line_num, line))
                i = end_idx + 1
                continue
            
            # Response handler: > {% ... %}
            if self.RESPONSE_HANDLER_START.match(stripped):
                script, end_idx = self._extract_script(lines, i)
                tokens.append(Token(TokenType.RESPONSE_HANDLER, script, line_num, line))
                i = end_idx + 1
                continue
            
            # Request line: METHOD URL [HTTP/version]
            match = self.REQUEST_LINE.match(stripped)
            if match:
                tokens.append(Token(
                    TokenType.REQUEST_LINE,
                    stripped, line_num, line,
                    method=match.group(1).upper(),
                    url=match.group(2)
                ))
                i += 1
                continue
            
            # Header: Name: Value
            match = self.HEADER.match(stripped)
            if match:
                tokens.append(Token(
                    TokenType.HEADER,
                    stripped, line_num, line,
                    header_name=match.group(1),
                    header_value=match.group(2).strip()
                ))
                i += 1
                continue
            
            # Default: body line
            tokens.append(Token(TokenType.BODY_LINE, line, line_num, line))
            i += 1
        
        return tokens
    
    def _extract_script(self, lines: list[str], start_idx: int) -> tuple[str, int]:
        """Extract script content between {% and %}."""
        script_lines = []
        i = start_idx
        in_script = False
        
        while i < len(lines):
            line = lines[i]
            if '{%' in line:
                in_script = True
                # Get content after {%
                idx = line.index('{%')
                after = line[idx + 2:]
                if '%}' in after:
                    # Single line script
                    end_idx = after.index('%}')
                    script_lines.append(after[:end_idx].strip())
                    return '\n'.join(script_lines), i
                script_lines.append(after)
            elif in_script:
                if '%}' in line:
                    idx = line.index('%}')
                    script_lines.append(line[:idx])
                    return '\n'.join(script_lines), i
                script_lines.append(line)
            i += 1
        
        return '\n'.join(script_lines), i - 1


@dataclass
class ParsedRequest:
    """Intermediate parsed request before variable resolution."""
    name: str | None = None
    method: str = ""
    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str | None = None
    directives: dict[str, str] = field(default_factory=dict)
    pre_request_script: str | None = None
    response_handler: str | None = None


class HttpParser:
    """Parser for .http files using lexer tokens."""
    
    def __init__(self, variable_manager: VariableManager | None = None):
        self.variables = variable_manager or VariableManager()
        self.lexer = HttpLexer()
    
    def parse_file(self, path: str | Path) -> HttpFile:
        """Parse a .http file."""
        path = Path(path)
        with open(path, encoding='utf-8') as f:
            content = f.read()
        
        http_file = self.parse_content(content)
        http_file.file_path = str(path)
        
        # Load environment files from same directory
        self._load_env_files(path.parent)
        
        return http_file
    
    def _load_env_files(self, directory: Path) -> None:
        """Load environment files from directory."""
        # .env file
        env_path = directory / '.env'
        if env_path.exists():
            self.variables.load_env_file(env_path)
        
        # http-client.env.json (JetBrains format)
        http_client_env = directory / 'http-client.env.json'
        if http_client_env.exists():
            self.variables.load_http_client_env(http_client_env)
        
        # http-client.private.env.json (JetBrains private env)
        private_env = directory / 'http-client.private.env.json'
        if private_env.exists():
            self.variables.load_http_client_env(private_env)
    
    def parse_content(self, content: str) -> HttpFile:
        """Parse .http file content."""
        tokens = self.lexer.tokenize(content)
        return self._parse_tokens(tokens)
    
    def _parse_tokens(self, tokens: list[Token]) -> HttpFile:
        """Parse tokens into HttpFile."""
        http_file = HttpFile()
        
        # First pass: extract global variables (before first separator or request)
        global_vars = self._extract_global_variables(tokens)
        http_file.variables = global_vars
        self.variables.set_many(global_vars)
        
        # Split tokens into request blocks
        blocks = self._split_into_blocks(tokens)
        
        # Parse each block
        for block in blocks:
            request = self._parse_block(block)
            if request:
                http_file.requests.append(request)
        
        return http_file
    
    def _extract_global_variables(self, tokens: list[Token]) -> dict[str, str]:
        """Extract variables defined before first request or separator."""
        variables = {}
        for token in tokens:
            if token.type == TokenType.SEPARATOR:
                break
            if token.type == TokenType.REQUEST_LINE:
                break
            if token.type == TokenType.VARIABLE_DEF:
                variables[token.var_name] = token.var_value
        return variables
    
    def _split_into_blocks(self, tokens: list[Token]) -> list[list[Token]]:
        """Split tokens into request blocks by separators."""
        blocks: list[list[Token]] = []
        current_block: list[Token] = []
        
        for token in tokens:
            if token.type == TokenType.SEPARATOR:
                if current_block:
                    blocks.append(current_block)
                # Start new block with separator (name comes from separator value)
                current_block = [token]
            else:
                current_block.append(token)
        
        if current_block:
            blocks.append(current_block)
        
        return blocks
    
    def _parse_block(self, tokens: list[Token]) -> HttpRequest | None:
        """Parse a block of tokens into an HttpRequest."""
        parsed = ParsedRequest()
        
        # Check if first token is separator (contains request name)
        if tokens and tokens[0].type == TokenType.SEPARATOR:
            parsed.name = tokens[0].value if tokens[0].value else None
            tokens = tokens[1:]
        
        # Extract block-level variables
        for token in tokens:
            if token.type == TokenType.VARIABLE_DEF:
                self.variables.set(token.var_name, token.var_value)
        
        # Find directives before request line
        for token in tokens:
            if token.type == TokenType.DIRECTIVE:
                parsed.directives[token.directive_name] = token.directive_value
            elif token.type == TokenType.REQUEST_LINE:
                break
        
        # Use # @name directive if present (overrides ### name)
        if "name" in parsed.directives:
            parsed.name = parsed.directives["name"]
        
        # Find request line
        request_line_idx = None
        for i, token in enumerate(tokens):
            if token.type == TokenType.REQUEST_LINE:
                parsed.method = token.method
                parsed.url = token.url
                request_line_idx = i
                break
        
        if request_line_idx is None:
            return None
        
        # Parse headers (after request line until empty line or body)
        in_headers = True
        body_lines = []
        
        for i in range(request_line_idx + 1, len(tokens)):
            token = tokens[i]
            
            if in_headers:
                if token.type == TokenType.HEADER:
                    parsed.headers[token.header_name] = token.header_value
                elif token.type == TokenType.EMPTY:
                    in_headers = False
                elif token.type == TokenType.BODY_LINE:
                    in_headers = False
                    body_lines.append(token.value)
                elif token.type in (TokenType.COMMENT, TokenType.DIRECTIVE):
                    continue  # Skip comments in header section
                else:
                    in_headers = False
                    if token.type == TokenType.BODY_LINE:
                        body_lines.append(token.value)
            else:
                if token.type == TokenType.BODY_LINE:
                    body_lines.append(token.value)
                elif token.type == TokenType.EMPTY:
                    body_lines.append("")
        
        # Join body lines
        if body_lines:
            body_text = '\n'.join(body_lines).strip()
            if body_text:
                parsed.body = body_text
        
        # Resolve variables
        url = self.variables.resolve(parsed.url)
        headers = {k: self.variables.resolve(v) for k, v in parsed.headers.items()}
        body = self.variables.resolve(parsed.body) if parsed.body else None
        
        # Create auth config from directives
        auth = self._create_auth_config(parsed.directives, headers)
        
        return HttpRequest(
            method=parsed.method,
            url=url,
            headers=headers,
            body=body,
            name=parsed.name,
            auth=auth,
        )
    
    def _create_auth_config(
        self, 
        directives: dict[str, str], 
        headers: dict[str, str]
    ) -> AuthConfig | None:
        """Create auth config from directives or headers."""
        # Check for sign directive: # @sign: ed25519 or # @sign: cobo
        sign_type = directives.get("sign", "").lower()
        
        if sign_type in ("ed25519", "cobo"):
            api_key = self.variables.get("api_key")
            api_secret = self.variables.get("api_secret")
            if api_key and api_secret:
                return AuthConfig(
                    type=AuthType.ED25519,
                    api_key=api_key,
                    api_secret=api_secret,
                )
        
        # Check Authorization header
        auth_header = headers.get('Authorization', '')
        
        if auth_header.lower().startswith('basic '):
            return AuthConfig(type=AuthType.BASIC, token=auth_header[6:])
        
        if auth_header.lower().startswith('bearer '):
            return AuthConfig(type=AuthType.BEARER, token=auth_header[7:])
        
        # Check for API key headers
        api_key_headers = ['X-API-Key', 'X-Api-Key', 'x-api-key', 'Api-Key', 'api-key']
        for key in api_key_headers:
            if key in headers:
                return AuthConfig(
                    type=AuthType.API_KEY,
                    api_key=headers[key],
                    api_key_name=key,
                    api_key_in='header'
                )
        
        return None


# Keep backward compatibility
class HttpFileParser(HttpParser):
    """Alias for backward compatibility."""
    pass


def parse_http_file(path: str | Path, variable_manager: VariableManager | None = None) -> HttpFile:
    """Convenience function to parse a .http file."""
    parser = HttpParser(variable_manager)
    return parser.parse_file(path)

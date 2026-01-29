# httpgo

A powerful HTTP command-line tool that supports `.http` files, inspired by [httpie](https://httpie.io/).

Built with [Typer](https://typer.fastapi.org.cn/) for a great CLI experience.

## Features

- 📁 **`.http` file support** - Parse and execute requests from `.http`/`.rest` files (VS Code REST Client format)
- 🔄 **Multiple requests** - Execute single or all requests from a file
- 📝 **Variables** - Support for file variables, environment variables, and dynamic variables
- 🔐 **Authentication** - Basic, Bearer, API Key, and Digest authentication
- 🎨 **Beautiful output** - Colorized, httpie-style output with syntax highlighting
- ⚡ **Fast** - Built on httpx for high performance
- 🐚 **Shell completion** - Auto-completion for Bash, Zsh, Fish, and PowerShell

## Installation

```bash
# Install with pip
pip install -e .

# Or using uv
uv pip install -e .
```

## Usage

### Running `.http` files

```bash
# Run first request in file
httpgo run api.http

# Run all requests
httpgo run api.http --all

# Run specific request by name
httpgo run api.http --name "Get User"

# Run specific request by index
httpgo run api.http --index 2

# With variables
httpgo run api.http -v baseUrl=http://localhost:3000 -v token=abc123

# With environment file
httpgo run api.http --env .env.local
```

### Direct HTTP requests (httpie-style)

```bash
# GET request
httpgo get https://httpbin.org/get

# POST with JSON data
httpgo post https://httpbin.org/post name=John age:=30

# POST with form data
httpgo post https://httpbin.org/post --form name=John email=john@example.com

# With headers
httpgo get https://api.example.com/data -H "Authorization: Bearer token123"

# With authentication
httpgo get https://api.example.com/data -a user:password
httpgo get https://api.example.com/data -a mytoken --auth-type bearer
```

### List requests in a file

```bash
httpgo list api.http
```

## `.http` File Format

```http
# Variables
@baseUrl = https://api.example.com
@token = your-api-token

### Get all users
GET {{baseUrl}}/users
Authorization: Bearer {{token}}

### Create a user
POST {{baseUrl}}/users
Content-Type: application/json
Authorization: Bearer {{token}}

{
    "name": "John Doe",
    "email": "john@example.com"
}

### Get user by ID
GET {{baseUrl}}/users/{{$uuid}}
```

### Variable Types

1. **File Variables**: Defined with `@name = value`
2. **Environment Variables**: From system environment or `.env` file
3. **Dynamic Variables**:
   - `{{$uuid}}` / `{{$guid}}` - Random UUID
   - `{{$timestamp}}` - Unix timestamp
   - `{{$isoTimestamp}}` - ISO 8601 timestamp
   - `{{$randomInt}}` - Random integer (0-1000)
   - `{{$randomString}}` - Random 10-character string

### Environment Files

httpgo supports `http-client.env.json` (VS Code REST Client format):

```json
{
    "$shared": {
        "apiVersion": "v1"
    },
    "dev": {
        "baseUrl": "http://localhost:3000",
        "token": "dev-token"
    },
    "prod": {
        "baseUrl": "https://api.example.com",
        "token": "prod-token"
    }
}
```

## Output Options

```bash
# Verbose mode (show request details)
httpgo run api.http --verbose

# Quiet mode (only show response body)
httpgo run api.http --quiet

# Show only headers
httpgo run api.http --headers

# Show only body
httpgo run api.http --body

# Disable colors
httpgo run api.http --no-color
```

## Authentication

### Basic Auth
```http
GET https://api.example.com/data
Authorization: Basic dXNlcjpwYXNz
```

Or via CLI:
```bash
httpgo get https://api.example.com/data -a user:password
```

### Bearer Token
```http
GET https://api.example.com/data
Authorization: Bearer your-token-here
```

Or via CLI:
```bash
httpgo get https://api.example.com/data -a your-token --auth-type bearer
```

### API Key
```http
GET https://api.example.com/data
X-API-Key: your-api-key
```

## Options

| Option | Description |
|--------|-------------|
| `--verbose` | Show request details |
| `--quiet, -q` | Only show response body |
| `--no-color` | Disable colored output |
| `--timeout, -t` | Request timeout in seconds (default: 30) |
| `--insecure, -k` | Disable SSL verification |
| `--env, -e` | Path to .env file |
| `--var, -v` | Set variable: name=value |

## Shell Completion

httpgo supports auto-completion for Bash, Zsh, Fish, and PowerShell.

```bash
# Install completion for your current shell
httpgo --install-completion

# Show completion script (to customize)
httpgo --show-completion
```

After installing, restart your shell or source the completion script.

## License

MIT

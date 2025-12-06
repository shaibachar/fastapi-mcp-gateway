# fastapi-mcp-gateway

Zero-boilerplate library to expose REST APIs and GraphQL APIs as MCP (Model Context Protocol) servers.

## Overview

`fastapi-mcp-gateway` provides runtime conversion of FastAPI, OpenAPI 3.x REST APIs, and GraphQL APIs into MCP servers, allowing AI agents to easily interact with your APIs. No code generation, no extra build steps - just pure runtime magic.

## Features

- 🚀 **Zero Boilerplate**: Minimal setup required
- 🔄 **Runtime Conversion**: No code generation step needed
- 🎯 **FastAPI First**: Optimized for FastAPI, but works with any OpenAPI 3.x API
- 🔷 **GraphQL Support**: Full support for GraphQL queries and mutations
- 🔌 **Multiple Modes**: In-process, HTTP, or GraphQL execution
- 🛠️ **MCP Client**: Built-in client for programmatic tool calls
- ⚙️ **Configurable**: Fine-grained control over exposed endpoints
- 🧪 **Well Tested**: Comprehensive unit and integration tests

## Installation

```bash
pip install fastapi-mcp-gateway
```

For FastAPI support:
```bash
pip install "fastapi-mcp-gateway[fastapi]"
```

For GraphQL support:
```bash
pip install "fastapi-mcp-gateway[graphql]"
```

For development:
```bash
pip install "fastapi-mcp-gateway[dev]"
```

## Quick Start

### Basic FastAPI Example

```python
from fastapi import FastAPI
from fastapi_mcp_gateway import create_mcp_server_from_fastapi

# Create your FastAPI app
app = FastAPI()

@app.get("/users")
def get_users(page: int = 1, limit: int = 10):
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

@app.post("/users")
def create_user(name: str, email: str):
    return {"id": 3, "name": name, "email": email}

# Create and run MCP server
if __name__ == "__main__":
    import asyncio
    
    mcp_server = create_mcp_server_from_fastapi(app)
    asyncio.run(mcp_server.run())
```

### Using an External OpenAPI URL

```python
import asyncio
from fastapi_mcp_gateway import create_mcp_server_from_openapi
from fastapi_mcp_gateway.config import GatewayConfig

async def main():
    # Create MCP server from external API
    mcp_server = await create_mcp_server_from_openapi(
        "http://localhost:8000/openapi.json",
        config=GatewayConfig(
            base_url="http://localhost:8000"
        )
    )
    
    await mcp_server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using the MCP Client

```python
import asyncio
from fastapi_mcp_gateway import MCPClient

async def main():
    # Connect to an MCP server
    client = MCPClient()
    await client.connect(
        command="python",
        args=["server.py"]
    )
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[t['name'] for t in tools]}")
    
    # Call a tool
    result = await client.call_tool(
        "get_users",
        {"page": 1, "limit": 10}
    )
    print(f"Result: {result}")
    
    # Cleanup
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

### Using a GraphQL API

```python
import asyncio
from fastapi_mcp_gateway import create_mcp_server_from_graphql
from fastapi_mcp_gateway.config import GatewayConfig, GraphQLOperationFilter

async def main():
    # Create MCP server from GraphQL endpoint
    config = GatewayConfig(
        # Filter operations: ALL, QUERIES_ONLY, or MUTATIONS_ONLY
        graphql_operation_filter=GraphQLOperationFilter.ALL,
    )
    
    mcp_server = await create_mcp_server_from_graphql(
        "http://localhost:8000/graphql",
        config=config
    )
    
    await mcp_server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

The `GatewayConfig` class provides extensive configuration options:

### REST API Configuration

```python
from fastapi_mcp_gateway import create_mcp_server_from_fastapi, GatewayConfig
from fastapi_mcp_gateway.config import ExecutionMode
import logging

config = GatewayConfig(
    # Execution mode: IN_PROCESS (direct calls), HTTP (via requests), or GRAPHQL
    mode=ExecutionMode.IN_PROCESS,
    
    # Base URL for HTTP/GraphQL mode
    base_url="http://localhost:8000",
    
    # Include only specific paths (None = all)
    include_paths=["/api/*", "/public"],
    
    # Exclude specific paths
    exclude_paths=["/admin/*", "/internal"],
    
    # Custom authentication
    auth_factory=lambda: {"Authorization": "Bearer token123"},
    
    # Logging level
    log_level=logging.DEBUG,
    
    # HTTP timeout in seconds
    timeout=30.0,
    
    # Maximum retries for HTTP requests
    max_retries=3
)

mcp_server = create_mcp_server_from_fastapi(app, config=config)
```

### GraphQL Configuration

```python
from fastapi_mcp_gateway import create_mcp_server_from_graphql, GatewayConfig
from fastapi_mcp_gateway.config import GraphQLOperationFilter

config = GatewayConfig(
    # Filter which operations to expose
    graphql_operation_filter=GraphQLOperationFilter.ALL,  # or QUERIES_ONLY, MUTATIONS_ONLY
    
    # Include/exclude specific operations by name
    include_operations=["user", "users", "createUser"],
    exclude_operations=["deleteUser"],
    
    # GraphQL endpoint path (default: "/graphql")
    graphql_endpoint="/graphql",
)

mcp_server = await create_mcp_server_from_graphql(
    "http://localhost:8000/graphql",
    config=config
)
```

## How It Works

### REST APIs

1. **Schema Loading**: The library loads your OpenAPI schema (from FastAPI app or URL)
2. **Tool Mapping**: Each API endpoint is converted to an MCP tool with:
   - Tool name (from `operationId` or method+path)
   - Description (from `summary` and `description`)
   - Input schema (from path/query/body parameters)
3. **Execution**: When a tool is called, the library:
   - Resolves path parameters
   - Separates query params and request body
   - Makes the HTTP call or calls FastAPI directly
   - Returns the JSON response

### GraphQL APIs

1. **Schema Loading**: The library introspects your GraphQL schema
2. **Tool Mapping**: Each query/mutation is converted to an MCP tool with:
   - Tool name (from operation name)
   - Description (from field description)
   - Input schema (from GraphQL arguments)
3. **Execution**: When a tool is called, the library:
   - Builds a GraphQL query/mutation with variables
   - Sends HTTP POST to the GraphQL endpoint
   - Parses the response and handles errors
   - Returns the JSON data

## Path Filtering

Control which endpoints are exposed using include/exclude patterns:

```python
config = GatewayConfig(
    # Only expose /api/* endpoints
    include_paths=["/api/*"],
    
    # Exclude admin endpoints
    exclude_paths=["/api/admin/*"]
)
```

Pattern matching supports:
- Exact match: `/users`
- Prefix wildcard: `/api/*`
- Suffix wildcard: `*/admin`

## Execution Modes

### In-Process Mode (Default)

Calls your FastAPI app directly using `TestClient`:

```python
config = GatewayConfig(mode=ExecutionMode.IN_PROCESS)
mcp_server = create_mcp_server_from_fastapi(app, config=config)
```

**Advantages**: Faster, no network overhead, easier debugging  
**Use when**: Running MCP server alongside your FastAPI app

### HTTP Mode

Makes actual HTTP requests to your running API:

```python
config = GatewayConfig(
    mode=ExecutionMode.HTTP,
    base_url="http://localhost:8000"
)
mcp_server = await create_mcp_server_from_openapi(
    "http://localhost:8000/openapi.json",
    config=config
)
```

**Advantages**: Works with any HTTP API, supports remote servers  
**Use when**: API is already deployed, or you need realistic HTTP behavior

### GraphQL Mode

Executes GraphQL operations via HTTP POST:

```python
config = GatewayConfig(
    mode=ExecutionMode.GRAPHQL,
    base_url="http://localhost:8000/graphql"
)
mcp_server = await create_mcp_server_from_graphql(
    "http://localhost:8000/graphql",
    config=config
)
```

**Advantages**: Native GraphQL support, introspection, type-safe  
**Use when**: Working with GraphQL APIs, need queries and mutations as tools

## Authentication

Add authentication headers using the `auth_factory`:

```python
def get_auth_headers():
    return {
        "Authorization": f"Bearer {get_current_token()}",
        "X-API-Key": "secret-key"
    }

config = GatewayConfig(auth_factory=get_auth_headers)
```

## Development

### Setup

```bash
git clone https://github.com/yourusername/fastapi-mcp-gateway.git
cd fastapi-mcp-gateway
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fastapi_mcp_gateway --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy fastapi_mcp_gateway
```

## Project Structure

```
fastapi-mcp-gateway/
├── fastapi_mcp_gateway/
│   ├── __init__.py              # Public API
│   ├── config.py                # Configuration classes
│   ├── openapi_loader.py        # OpenAPI schema loading
│   ├── graphql_loader.py        # GraphQL schema loading
│   ├── mapping.py               # OpenAPI to MCP mapping
│   ├── graphql_mapping.py       # GraphQL to MCP mapping
│   ├── execution.py             # REST tool execution logic
│   ├── graphql_execution.py     # GraphQL tool execution
│   ├── mcp_server.py            # MCP server implementation
│   └── mcp_client.py            # MCP client wrapper
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── examples/
│   ├── simple_server.py         # FastAPI REST example
│   ├── graphql_server.py        # GraphQL server example
│   ├── graphql_mcp_server.py    # GraphQL MCP server
│   └── graphql_client.py        # GraphQL MCP client
├── spec/
│   └── design.md                # Design specification
├── pyproject.toml               # Package configuration
└── README.md                    # This file
```

## Limitations (v1)

- JSON content types only (no multipart/form-data, etc.)
- No WebSocket or SSE support
- No typed client generation
- Basic authentication support only
- GraphQL subscriptions not supported
- GraphQL fragments and directives not supported

## Roadmap

- [ ] WebSocket and SSE support
- [ ] GraphQL subscriptions (via WebSocket)
- [ ] GraphQL fragments and directives
- [ ] GraphQL federation support
- [ ] Semantic tool descriptions enhancement
- [ ] Typed client generation (REST + GraphQL)
- [ ] CLI launcher for easy deployment
- [ ] Support for more content types
- [ ] Advanced authentication flows (OAuth2, etc.)
- [ ] Hybrid REST + GraphQL endpoints
- [ ] GraphQL query optimization and batching

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [MCP](https://github.com/modelcontextprotocol) - Model Context Protocol
- [httpx](https://www.python-httpx.org/) - HTTP client
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
Python library that dynamically generates an MCP server and client from REST endpoints, using a FastAPI (or any OpenAPI-compatible) app as the source of truth.

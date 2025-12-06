# fastapi-mcp-gateway: Design Specification

## 1. High-Level Overview

### 1.1 Purpose

Provide a zero/low-boilerplate way to expose an existing REST API (FastAPI or any OpenAPI 3.x service) as:

1. An MCP server with tools generated at runtime from the REST endpoints.
2. An optional MCP client wrapper that lets Python code or agent frameworks call these tools easily.

Goals:

- Runtime-only: NO code generation step, no extra build-time artifacts.
- Minimal user code: For FastAPI, ideally:

```python
from fastapi import FastAPI
from fastapi_mcp_gateway import create_mcp_server

app = FastAPI()
# define routes ...
mcp_server = create_mcp_server(app)
mcp_server.run()
```

- Use the app’s OpenAPI schema to:
  - discover endpoints
  - build MCP tool definitions
  - map MCP tool calls → HTTP calls → JSON responses

## 2. Scope

### 2.1 In Scope

- FastAPI (primary)
- Generic OpenAPI 3.0/3.1 support
- MCP server generation
- MCP client wrapper
- Basic configuration
- Unit testing and integration testing

### 2.2 Out of Scope (v1)

- WebSocket/SSE
- Non-JSON content types
- Typed client generation
- Advanced auth flows

## 3. Architecture

Components:
- OpenAPI Loader
- Mapping Layer
- MCP Server
- MCP Client

## 4. Public API Design

### FastAPI helper

```python
from fastapi_mcp_gateway import create_mcp_server_from_fastapi

mcp_server = create_mcp_server_from_fastapi(app)
```

### Generic OpenAPI helper

```python
from fastapi_mcp_gateway import create_mcp_server_from_openapi

mcp_server = create_mcp_server_from_openapi("http://localhost:8000/openapi.json")
```

### Client

```python
from fastapi_mcp_gateway import MCPClient

client = MCPClient()
await client.call_tool("get_users", {"page": 1})
```

## 5. Mapping Rules

- Tool name from operationId or method+path
- Description uses summary + description
- Input parameters merged from path/query/body
- Output schema from 200 JSON content

## 6. Execution Flow

Tool → handler → HTTP/in-process → return JSON.

## 7. Configuration

Config dataclass with:
- mode
- base_url
- include/exclude paths
- auth factory
- logging

## 8. Package Layout

```
fastapi_mcp_gateway/
    openapi_loader.py
    mapping.py
    mcp_server.py
    mcp_client.py
    execution.py
tests/
    unit/
    integration/
```

## 9. Testing Strategy

### Unit Tests

- test_openapi_loader
- test_mapping
- test_execution_inprocess
- test_execution_http
- test_config_defaults
- test_mcp_server_registration
- test_mcp_client_stub

### Integration Tests

- test_mcp_with_fastapi_inprocess
- test_mcp_with_fastapi_http
- test_client_server_roundtrip

## 10. Future Extensions

- WebSocket support
- Semantic tool descriptions
- Typed client generation
- CLI launcher

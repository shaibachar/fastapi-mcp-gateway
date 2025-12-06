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

- Use the app's OpenAPI schema or GraphQL schema to:
  - discover endpoints (REST) or queries/mutations (GraphQL)
  - build MCP tool definitions
  - map MCP tool calls → HTTP calls / GraphQL queries → JSON responses

## 2. Scope

### 2.1 In Scope

- FastAPI (primary)
- Generic OpenAPI 3.0/3.1 support
- GraphQL endpoint support (queries and mutations)
- GraphQL schema introspection
- MCP server generation
- MCP client wrapper
- Basic configuration
- Unit testing and integration testing

### 2.2 Out of Scope (v1)

- WebSocket/SSE
- Non-JSON content types
- Typed client generation
- Advanced auth flows
- GraphQL subscriptions
- GraphQL fragments and directives

## 3. Architecture

Components:
- OpenAPI Loader
- GraphQL Schema Loader
- Mapping Layer (REST & GraphQL)
- MCP Server
- MCP Client
- Execution Layer (HTTP & GraphQL)

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

### GraphQL helper

```python
from fastapi_mcp_gateway import create_mcp_server_from_graphql

# From introspection endpoint
mcp_server = await create_mcp_server_from_graphql("http://localhost:8000/graphql")

# From schema file
mcp_server = create_mcp_server_from_graphql_schema("schema.graphql")
```

### Client

```python
from fastapi_mcp_gateway import MCPClient

client = MCPClient()
await client.call_tool("get_users", {"page": 1})
```

## 5. Mapping Rules

### REST (OpenAPI)

- Tool name from operationId or method+path
- Description uses summary + description
- Input parameters merged from path/query/body
- Output schema from 200 JSON content

### GraphQL

- Tool name from query/mutation name (e.g., "getUser", "createUser")
- Description from GraphQL field description
- Input parameters from GraphQL arguments
- Output schema from GraphQL return type
- Queries mapped as read-only tools
- Mutations mapped as write tools

## 6. Execution Flow

### REST

Tool → handler → HTTP/in-process → return JSON.

### GraphQL

Tool → build query/mutation → HTTP POST to /graphql → parse response → return JSON.

GraphQL execution details:
1. Tool arguments converted to GraphQL variables
2. Query/mutation string constructed with operation name and fields
3. HTTP POST to GraphQL endpoint with query and variables
4. Response data extracted and errors handled
5. Return JSON result

## 7. Configuration

Config dataclass with:
- mode (in_process, http, graphql)
- base_url
- include/exclude paths (for REST) or operations (for GraphQL)
- auth factory
- logging
- graphql_endpoint (default: "/graphql")
- graphql_operation_filter (queries_only, mutations_only, all)

## 8. Package Layout

```
fastapi_mcp_gateway/
    openapi_loader.py
    graphql_loader.py
    graphql_mapping.py
    graphql_execution.py
    mapping.py
    mcp_server.py
    mcp_client.py
    execution.py
tests/
    unit/
        test_graphql_loader.py
        test_graphql_mapping.py
        test_graphql_execution.py
    integration/
        test_graphql_integration.py
```

## 9. Testing Strategy

### Unit Tests

- test_openapi_loader
- test_graphql_loader
- test_graphql_schema_introspection
- test_graphql_mapping_queries
- test_graphql_mapping_mutations
- test_mapping
- test_execution_inprocess
- test_execution_http
- test_execution_graphql
- test_config_defaults
- test_mcp_server_registration
- test_mcp_client_stub

### Integration Tests

- test_mcp_with_fastapi_inprocess
- test_mcp_with_fastapi_http
- test_mcp_with_graphql_endpoint
- test_graphql_queries_and_mutations
- test_client_server_roundtrip

## 10. Future Extensions

- WebSocket support
- GraphQL subscriptions (via WebSocket)
- GraphQL fragments and directives support
- GraphQL federation support
- Semantic tool descriptions
- Typed client generation (REST + GraphQL)
- CLI launcher
- Hybrid REST + GraphQL endpoints
- GraphQL query optimization and batching

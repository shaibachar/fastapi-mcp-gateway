"""
fastapi-mcp-gateway: Zero-boilerplate library to expose REST APIs as MCP servers.

This library provides runtime conversion of FastAPI or OpenAPI 3.x REST APIs
into MCP (Model Context Protocol) servers, allowing AI agents to easily interact
with your APIs.
"""

from fastapi_mcp_gateway.config import GatewayConfig
from fastapi_mcp_gateway.mcp_client import MCPClient
from fastapi_mcp_gateway.mcp_server import (
    create_mcp_server_from_fastapi,
    create_mcp_server_from_openapi,
)

__version__ = "0.1.0"

__all__ = [
    "GatewayConfig",
    "MCPClient",
    "create_mcp_server_from_fastapi",
    "create_mcp_server_from_openapi",
]

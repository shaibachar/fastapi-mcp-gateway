"""Integration tests for FastAPI MCP gateway."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_mcp_gateway import create_mcp_server_from_fastapi
from fastapi_mcp_gateway.config import GatewayConfig, ExecutionMode


@pytest.fixture
def sample_fastapi_app():
    """Create a sample FastAPI app for testing."""
    app = FastAPI(title="Test API", version="1.0.0")
    
    @app.get("/users")
    def get_users(page: int = 1, limit: int = 10):
        """Get all users."""
        return [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    
    @app.get("/users/{user_id}")
    def get_user(user_id: int):
        """Get a specific user."""
        return {"id": user_id, "name": f"User {user_id}"}
    
    @app.post("/users")
    def create_user(name: str, email: str):
        """Create a new user."""
        return {"id": 3, "name": name, "email": email}
    
    return app


def test_create_mcp_server_from_fastapi(sample_fastapi_app):
    """Test creating an MCP server from a FastAPI app."""
    server = create_mcp_server_from_fastapi(sample_fastapi_app)
    
    assert server is not None
    assert server.fastapi_app == sample_fastapi_app
    assert len(server.tools) > 0


def test_mcp_server_tools_count(sample_fastapi_app):
    """Test that all endpoints are converted to tools."""
    server = create_mcp_server_from_fastapi(sample_fastapi_app)
    
    # Should have 3 tools: get /users, get /users/{id}, post /users
    assert len(server.tools) == 3


def test_mcp_server_with_path_filtering(sample_fastapi_app):
    """Test MCP server with path filtering."""
    config = GatewayConfig(
        mode=ExecutionMode.IN_PROCESS,
        include_paths=["/users"]
    )
    server = create_mcp_server_from_fastapi(sample_fastapi_app, config=config)
    
    # Should only include exact match /users
    assert len(server.tools) == 1
    assert server.tools[0]["_metadata"]["path"] == "/users"


def test_mcp_server_with_exclude_paths(sample_fastapi_app):
    """Test MCP server with exclude paths."""
    config = GatewayConfig(
        mode=ExecutionMode.IN_PROCESS,
        exclude_paths=["/users/{user_id}"]
    )
    server = create_mcp_server_from_fastapi(sample_fastapi_app, config=config)
    
    # Should exclude /users/{user_id}
    assert len(server.tools) == 2
    paths = [t["_metadata"]["path"] for t in server.tools]
    assert "/users/{user_id}" not in paths


@pytest.mark.asyncio
async def test_tool_execution_in_process(sample_fastapi_app):
    """Test executing a tool in in-process mode."""
    server = create_mcp_server_from_fastapi(sample_fastapi_app)
    
    # Find the get_users tool
    get_users_tool = next(
        (t for t in server.tools if t["name"] == "get_users"),
        None
    )
    assert get_users_tool is not None
    
    # Execute the tool
    result = await server.executor.execute_tool(
        get_users_tool["_metadata"],
        {"page": 1, "limit": 10}
    )
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_tool_execution_with_path_param(sample_fastapi_app):
    """Test executing a tool with path parameters."""
    server = create_mcp_server_from_fastapi(sample_fastapi_app)
    
    # Find the get_user tool
    get_user_tool = next(
        (t for t in server.tools if "user_id" in t["name"]),
        None
    )
    assert get_user_tool is not None
    
    # Execute the tool
    result = await server.executor.execute_tool(
        get_user_tool["_metadata"],
        {"user_id": 42}
    )
    
    assert result["id"] == 42
    assert result["name"] == "User 42"


@pytest.mark.asyncio
async def test_tool_execution_post_request(sample_fastapi_app):
    """Test executing a POST tool."""
    server = create_mcp_server_from_fastapi(sample_fastapi_app)
    
    # Find the create_user tool
    create_user_tool = next(
        (t for t in server.tools if t["_metadata"]["method"] == "POST"),
        None
    )
    assert create_user_tool is not None
    
    # Execute the tool
    result = await server.executor.execute_tool(
        create_user_tool["_metadata"],
        {"name": "Charlie", "email": "charlie@example.com"}
    )
    
    assert result["name"] == "Charlie"
    assert result["email"] == "charlie@example.com"

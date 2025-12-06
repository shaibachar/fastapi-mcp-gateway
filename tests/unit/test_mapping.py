"""Unit tests for the mapping module."""

import pytest

from fastapi_mcp_gateway.mapping import OperationMapper


def test_generate_tool_name_with_operation_id():
    """Test tool name generation with operationId."""
    name = OperationMapper.generate_tool_name(
        "get", "/users", operation_id="getAllUsers"
    )
    assert name == "getallusers"


def test_generate_tool_name_without_operation_id():
    """Test tool name generation without operationId."""
    name = OperationMapper.generate_tool_name("get", "/users/{id}")
    assert name == "get_users_id"


def test_generate_tool_name_complex_path():
    """Test tool name generation with complex path."""
    name = OperationMapper.generate_tool_name("post", "/api/v1/users/{userId}/posts")
    assert name == "post_api_v1_users_userid_posts"


def test_extract_description_with_both():
    """Test description extraction with summary and description."""
    operation = {
        "summary": "Get users",
        "description": "Retrieves all users from the database"
    }
    desc = OperationMapper.extract_description(operation)
    assert desc == "Get users. Retrieves all users from the database"


def test_extract_description_with_summary_only():
    """Test description extraction with summary only."""
    operation = {"summary": "Get users"}
    desc = OperationMapper.extract_description(operation)
    assert desc == "Get users"


def test_extract_description_with_description_only():
    """Test description extraction with description only."""
    operation = {"description": "Retrieves all users"}
    desc = OperationMapper.extract_description(operation)
    assert desc == "Retrieves all users"


def test_extract_description_with_neither():
    """Test description extraction with no summary or description."""
    operation = {}
    desc = OperationMapper.extract_description(operation)
    assert desc == "No description available"


def test_extract_parameters_path_params():
    """Test parameter extraction with path parameters."""
    operation = {}
    schema = OperationMapper.extract_parameters(operation, "/users/{id}")
    
    assert "id" in schema["properties"]
    assert schema["properties"]["id"]["type"] == "string"
    assert "id" in schema["required"]


def test_extract_parameters_query_params():
    """Test parameter extraction with query parameters."""
    operation = {
        "parameters": [
            {
                "name": "page",
                "in": "query",
                "required": True,
                "schema": {"type": "integer"}
            }
        ]
    }
    schema = OperationMapper.extract_parameters(operation, "/users")
    
    assert "page" in schema["properties"]
    assert schema["properties"]["page"]["type"] == "integer"
    assert "page" in schema["required"]


def test_extract_parameters_request_body():
    """Test parameter extraction with request body."""
    operation = {
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string"}
                        },
                        "required": ["email"]
                    }
                }
            }
        }
    }
    schema = OperationMapper.extract_parameters(operation, "/users")
    
    assert "name" in schema["properties"]
    assert "email" in schema["properties"]
    assert "email" in schema["required"]


def test_extract_response_schema():
    """Test response schema extraction."""
    operation = {
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {"type": "object"}
                        }
                    }
                }
            }
        }
    }
    schema = OperationMapper.extract_response_schema(operation)
    
    assert schema is not None
    assert schema["type"] == "array"


def test_extract_response_schema_no_json():
    """Test response schema extraction with no JSON response."""
    operation = {
        "responses": {
            "200": {
                "description": "Success"
            }
        }
    }
    schema = OperationMapper.extract_response_schema(operation)
    assert schema is None


def test_map_operation_to_tool():
    """Test mapping a complete operation to a tool."""
    operation = {
        "operationId": "getUser",
        "summary": "Get a user",
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {"type": "integer"}
            }
        ],
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {"type": "object"}
                    }
                }
            }
        }
    }
    
    tool = OperationMapper.map_operation_to_tool("get", "/users/{id}", operation)
    
    assert tool["name"] == "getuser"
    assert tool["description"] == "Get a user"
    assert "id" in tool["inputSchema"]["properties"]
    assert "_metadata" in tool
    assert tool["_metadata"]["method"] == "GET"
    assert tool["_metadata"]["path"] == "/users/{id}"


def test_map_openapi_to_tools():
    """Test mapping entire OpenAPI schema to tools."""
    schema = {
        "openapi": "3.0.0",
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "summary": "Get all users"
                }
            },
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "summary": "Get a user"
                },
                "delete": {
                    "operationId": "deleteUser",
                    "summary": "Delete a user"
                }
            }
        }
    }
    
    tools = OperationMapper.map_openapi_to_tools(schema)
    
    assert len(tools) == 3
    tool_names = [t["name"] for t in tools]
    assert "getusers" in tool_names
    assert "getuser" in tool_names
    assert "deleteuser" in tool_names

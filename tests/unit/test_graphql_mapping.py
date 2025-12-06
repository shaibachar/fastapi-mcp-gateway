"""Unit tests for the GraphQL mapping module."""

import pytest

from fastapi_mcp_gateway.graphql_mapping import GraphQLOperationMapper


def test_generate_tool_name():
    """Test tool name generation."""
    name = GraphQLOperationMapper.generate_tool_name("getUser", "query")
    assert name == "getuser"

    name = GraphQLOperationMapper.generate_tool_name("createUser", "mutation")
    assert name == "createuser"


def test_extract_description():
    """Test description extraction."""
    field = {"name": "getUser", "description": "Get a user by ID"}
    desc = GraphQLOperationMapper.extract_description(field)
    assert desc == "Get a user by ID"

    field = {"name": "getUser"}
    desc = GraphQLOperationMapper.extract_description(field)
    assert "getUser" in desc


def test_extract_type_name():
    """Test type name extraction."""
    # Scalar type
    type_ref = {"kind": "SCALAR", "name": "String"}
    assert GraphQLOperationMapper.extract_type_name(type_ref) == "String"

    # NON_NULL wrapper
    type_ref = {
        "kind": "NON_NULL",
        "ofType": {"kind": "SCALAR", "name": "ID"},
    }
    assert GraphQLOperationMapper.extract_type_name(type_ref) == "ID"

    # LIST wrapper
    type_ref = {
        "kind": "LIST",
        "ofType": {"kind": "SCALAR", "name": "String"},
    }
    assert GraphQLOperationMapper.extract_type_name(type_ref) == "String"

    # Nested wrappers
    type_ref = {
        "kind": "NON_NULL",
        "ofType": {
            "kind": "LIST",
            "ofType": {
                "kind": "NON_NULL",
                "ofType": {"kind": "SCALAR", "name": "Int"},
            },
        },
    }
    assert GraphQLOperationMapper.extract_type_name(type_ref) == "Int"


def test_graphql_type_to_json_schema_type():
    """Test GraphQL to JSON Schema type conversion."""
    assert GraphQLOperationMapper.graphql_type_to_json_schema_type("String") == "string"
    assert GraphQLOperationMapper.graphql_type_to_json_schema_type("Int") == "integer"
    assert GraphQLOperationMapper.graphql_type_to_json_schema_type("Float") == "number"
    assert GraphQLOperationMapper.graphql_type_to_json_schema_type("Boolean") == "boolean"
    assert GraphQLOperationMapper.graphql_type_to_json_schema_type("ID") == "string"
    assert GraphQLOperationMapper.graphql_type_to_json_schema_type("Unknown") == "string"


def test_is_required():
    """Test required field detection."""
    type_ref = {"kind": "NON_NULL", "ofType": {"kind": "SCALAR", "name": "String"}}
    assert GraphQLOperationMapper.is_required(type_ref) is True

    type_ref = {"kind": "SCALAR", "name": "String"}
    assert GraphQLOperationMapper.is_required(type_ref) is False


def test_extract_arguments():
    """Test argument extraction."""
    field = {
        "name": "user",
        "args": [
            {
                "name": "id",
                "description": "User ID",
                "type": {
                    "kind": "NON_NULL",
                    "ofType": {"kind": "SCALAR", "name": "ID"},
                },
            },
            {
                "name": "includeDetails",
                "description": "Include detailed info",
                "type": {"kind": "SCALAR", "name": "Boolean"},
                "defaultValue": "false",
            },
        ],
    }

    schema = GraphQLOperationMapper.extract_arguments(field)

    assert "id" in schema["properties"]
    assert "includeDetails" in schema["properties"]
    assert schema["properties"]["id"]["type"] == "string"
    assert schema["properties"]["includeDetails"]["type"] == "boolean"
    assert "id" in schema["required"]
    assert "includeDetails" not in schema["required"]
    assert schema["properties"]["includeDetails"]["default"] == "false"


def test_map_operation_to_tool_query():
    """Test mapping a query to a tool."""
    field = {
        "name": "getUser",
        "description": "Get a user by ID",
        "args": [
            {
                "name": "id",
                "type": {
                    "kind": "NON_NULL",
                    "ofType": {"kind": "SCALAR", "name": "ID"},
                },
            }
        ],
        "type": {"kind": "OBJECT", "name": "User"},
    }

    tool = GraphQLOperationMapper.map_operation_to_tool(field, "query")

    assert tool["name"] == "getuser"
    assert "[QUERY]" in tool["description"]
    assert "id" in tool["inputSchema"]["properties"]


def test_map_operation_to_tool_mutation():
    """Test mapping a mutation to a tool."""
    field = {
        "name": "createUser",
        "description": "Create a new user",
        "args": [
            {
                "name": "name",
                "type": {
                    "kind": "NON_NULL",
                    "ofType": {"kind": "SCALAR", "name": "String"},
                },
            }
        ],
        "type": {"kind": "OBJECT", "name": "User"},
    }

    tool = GraphQLOperationMapper.map_operation_to_tool(field, "mutation")

    assert tool["name"] == "createuser"
    assert "[MUTATION]" in tool["description"]
    assert "name" in tool["inputSchema"]["properties"]


def test_build_query_string():
    """Test GraphQL query string building."""
    field = {
        "name": "user",
        "args": [
            {
                "name": "id",
                "type": {
                    "kind": "NON_NULL",
                    "ofType": {"kind": "SCALAR", "name": "ID"},
                },
            }
        ],
    }

    query, variables = GraphQLOperationMapper.build_query_string(
        "user", "query", {"id": "123"}, field
    )

    assert "query" in query
    assert "user" in query
    assert "$id" in query
    assert variables == {"id": "123"}


def test_build_mutation_string():
    """Test GraphQL mutation string building."""
    field = {
        "name": "createUser",
        "args": [
            {
                "name": "name",
                "type": {
                    "kind": "NON_NULL",
                    "ofType": {"kind": "SCALAR", "name": "String"},
                },
            },
            {
                "name": "email",
                "type": {
                    "kind": "NON_NULL",
                    "ofType": {"kind": "SCALAR", "name": "String"},
                },
            },
        ],
    }

    query, variables = GraphQLOperationMapper.build_query_string(
        "createUser",
        "mutation",
        {"name": "Alice", "email": "alice@example.com"},
        field,
    )

    assert "mutation" in query
    assert "createUser" in query
    assert "$name" in query
    assert "$email" in query
    assert variables == {"name": "Alice", "email": "alice@example.com"}

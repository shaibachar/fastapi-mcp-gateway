"""Unit tests for the GraphQL loader."""

import pytest

from fastapi_mcp_gateway.graphql_loader import GraphQLLoader


@pytest.fixture
def sample_graphql_schema():
    """Sample GraphQL introspection schema."""
    return {
        "queryType": {"name": "Query"},
        "mutationType": {"name": "Mutation"},
        "types": [
            {
                "kind": "OBJECT",
                "name": "Query",
                "fields": [
                    {
                        "name": "user",
                        "description": "Get a user by ID",
                        "args": [
                            {
                                "name": "id",
                                "description": "User ID",
                                "type": {
                                    "kind": "NON_NULL",
                                    "ofType": {"kind": "SCALAR", "name": "ID"},
                                },
                            }
                        ],
                        "type": {"kind": "OBJECT", "name": "User"},
                    },
                    {
                        "name": "users",
                        "description": "Get all users",
                        "args": [],
                        "type": {
                            "kind": "LIST",
                            "ofType": {"kind": "OBJECT", "name": "User"},
                        },
                    },
                ],
            },
            {
                "kind": "OBJECT",
                "name": "Mutation",
                "fields": [
                    {
                        "name": "createUser",
                        "description": "Create a new user",
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
                        "type": {"kind": "OBJECT", "name": "User"},
                    }
                ],
            },
            {
                "kind": "OBJECT",
                "name": "User",
                "fields": [
                    {
                        "name": "id",
                        "type": {"kind": "SCALAR", "name": "ID"},
                    },
                    {
                        "name": "name",
                        "type": {"kind": "SCALAR", "name": "String"},
                    },
                    {
                        "name": "email",
                        "type": {"kind": "SCALAR", "name": "String"},
                    },
                ],
            },
        ],
    }


def test_load_from_dict(sample_graphql_schema):
    """Test loading schema from dictionary."""
    schema = GraphQLLoader.load_from_dict(sample_graphql_schema)

    assert schema["queryType"]["name"] == "Query"
    assert schema["mutationType"]["name"] == "Mutation"
    assert len(schema["types"]) == 3


def test_load_from_dict_invalid():
    """Test loading invalid schema."""
    with pytest.raises(ValueError, match="Schema must be a dictionary"):
        GraphQLLoader.load_from_dict("not a dict")

    with pytest.raises(ValueError, match="types"):
        GraphQLLoader.load_from_dict({"invalid": "schema"})


def test_get_query_type(sample_graphql_schema):
    """Test extracting Query type."""
    query_type = GraphQLLoader.get_query_type(sample_graphql_schema)

    assert query_type is not None
    assert query_type["name"] == "Query"
    assert len(query_type["fields"]) == 2


def test_get_mutation_type(sample_graphql_schema):
    """Test extracting Mutation type."""
    mutation_type = GraphQLLoader.get_mutation_type(sample_graphql_schema)

    assert mutation_type is not None
    assert mutation_type["name"] == "Mutation"
    assert len(mutation_type["fields"]) == 1


def test_get_queries(sample_graphql_schema):
    """Test extracting queries."""
    queries = GraphQLLoader.get_queries(sample_graphql_schema)

    assert len(queries) == 2
    assert queries[0]["name"] == "user"
    assert queries[1]["name"] == "users"


def test_get_mutations(sample_graphql_schema):
    """Test extracting mutations."""
    mutations = GraphQLLoader.get_mutations(sample_graphql_schema)

    assert len(mutations) == 1
    assert mutations[0]["name"] == "createUser"


def test_get_all_operations(sample_graphql_schema):
    """Test extracting all operations."""
    operations = GraphQLLoader.get_all_operations(sample_graphql_schema)

    assert "queries" in operations
    assert "mutations" in operations
    assert len(operations["queries"]) == 2
    assert len(operations["mutations"]) == 1


def test_get_query_type_no_queries():
    """Test when schema has no queries."""
    schema = {"types": []}
    query_type = GraphQLLoader.get_query_type(schema)

    assert query_type is None


def test_get_mutation_type_no_mutations():
    """Test when schema has no mutations."""
    schema = {"types": []}
    mutation_type = GraphQLLoader.get_mutation_type(schema)

    assert mutation_type is None

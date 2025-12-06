"""Unit tests for the OpenAPI loader."""

import json
import pytest

from fastapi_mcp_gateway.openapi_loader import OpenAPILoader


@pytest.fixture
def sample_openapi_schema():
    """Sample OpenAPI 3.0 schema."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://localhost:8000"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "getUsers",
                    "summary": "Get all users",
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        }
    }


def test_load_from_dict(sample_openapi_schema):
    """Test loading schema from dictionary."""
    schema = OpenAPILoader.load_from_dict(sample_openapi_schema)
    
    assert schema["openapi"] == "3.0.0"
    assert schema["info"]["title"] == "Test API"


def test_load_from_dict_invalid():
    """Test loading invalid schema."""
    with pytest.raises(ValueError, match="Schema must be a dictionary"):
        OpenAPILoader.load_from_dict("not a dict")
    
    with pytest.raises(ValueError, match="openapi.*swagger"):
        OpenAPILoader.load_from_dict({"invalid": "schema"})


def test_validate_schema_openapi_3(sample_openapi_schema):
    """Test validating OpenAPI 3.x schema."""
    OpenAPILoader.validate_schema(sample_openapi_schema)  # Should not raise


def test_validate_schema_swagger_2():
    """Test validating Swagger 2.0 schema."""
    schema = {"swagger": "2.0"}
    
    with pytest.warns():
        OpenAPILoader.validate_schema(schema)


def test_validate_schema_invalid():
    """Test validating invalid schema."""
    with pytest.raises(ValueError, match="Unsupported"):
        OpenAPILoader.validate_schema({"openapi": "1.0"})


def test_get_paths(sample_openapi_schema):
    """Test extracting paths from schema."""
    paths = OpenAPILoader.get_paths(sample_openapi_schema)
    
    assert "/users" in paths
    assert "get" in paths["/users"]


def test_get_servers(sample_openapi_schema):
    """Test extracting servers from schema."""
    servers = OpenAPILoader.get_servers(sample_openapi_schema)
    
    assert len(servers) == 1
    assert servers[0]["url"] == "http://localhost:8000"


def test_get_base_url(sample_openapi_schema):
    """Test extracting base URL from schema."""
    base_url = OpenAPILoader.get_base_url(sample_openapi_schema)
    
    assert base_url == "http://localhost:8000"


def test_get_base_url_no_servers():
    """Test extracting base URL when no servers defined."""
    schema = {"openapi": "3.0.0", "paths": {}}
    base_url = OpenAPILoader.get_base_url(schema)
    
    assert base_url is None

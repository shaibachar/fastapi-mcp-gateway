"""Unit tests for the config module."""

import logging
import pytest

from fastapi_mcp_gateway.config import ExecutionMode, GatewayConfig


def test_config_defaults():
    """Test default configuration values."""
    config = GatewayConfig()
    
    assert config.mode == ExecutionMode.IN_PROCESS
    assert config.base_url is None
    assert config.include_paths is None
    assert config.exclude_paths == []
    assert config.auth_factory is None
    assert config.log_level == logging.INFO
    assert config.timeout == 30.0
    assert config.max_retries == 3


def test_config_http_mode_requires_base_url():
    """Test that HTTP mode requires a base_url."""
    with pytest.raises(ValueError, match="base_url is required"):
        GatewayConfig(mode=ExecutionMode.HTTP)


def test_config_http_mode_with_base_url():
    """Test HTTP mode with base_url."""
    config = GatewayConfig(
        mode=ExecutionMode.HTTP,
        base_url="http://localhost:8000"
    )
    
    assert config.mode == ExecutionMode.HTTP
    assert config.base_url == "http://localhost:8000"


def test_config_in_process_mode_with_base_url_warning(caplog):
    """Test warning when base_url is set in IN_PROCESS mode."""
    with caplog.at_level(logging.WARNING):
        config = GatewayConfig(
            mode=ExecutionMode.IN_PROCESS,
            base_url="http://localhost:8000"
        )
    
    assert "base_url is set but mode is IN_PROCESS" in caplog.text
    assert config.mode == ExecutionMode.IN_PROCESS


def test_should_include_path_no_filters():
    """Test path inclusion with no filters (include all)."""
    config = GatewayConfig()
    
    assert config.should_include_path("/users")
    assert config.should_include_path("/api/v1/products")
    assert config.should_include_path("/admin/settings")


def test_should_include_path_with_exclude():
    """Test path inclusion with exclude patterns."""
    config = GatewayConfig(exclude_paths=["/admin/*", "/internal"])
    
    assert config.should_include_path("/users")
    assert config.should_include_path("/api/v1/products")
    assert not config.should_include_path("/admin/settings")
    assert not config.should_include_path("/admin/users")
    assert not config.should_include_path("/internal")


def test_should_include_path_with_include():
    """Test path inclusion with include patterns."""
    config = GatewayConfig(include_paths=["/api/*", "/public"])
    
    assert not config.should_include_path("/users")
    assert config.should_include_path("/api/v1/products")
    assert config.should_include_path("/api/users")
    assert config.should_include_path("/public")
    assert not config.should_include_path("/admin")


def test_should_include_path_with_both_filters():
    """Test path inclusion with both include and exclude patterns."""
    config = GatewayConfig(
        include_paths=["/api/*"],
        exclude_paths=["/api/admin/*"]
    )
    
    assert config.should_include_path("/api/users")
    assert config.should_include_path("/api/products")
    assert not config.should_include_path("/api/admin/settings")
    assert not config.should_include_path("/users")


def test_pattern_matching():
    """Test pattern matching logic."""
    config = GatewayConfig()
    
    # Exact match
    assert config._match_pattern("/users", "/users")
    assert not config._match_pattern("/users/1", "/users")
    
    # Prefix match
    assert config._match_pattern("/api/users", "/api/*")
    assert config._match_pattern("/api/v1/users", "/api/*")
    assert not config._match_pattern("/users", "/api/*")
    
    # Suffix match
    assert config._match_pattern("/api/admin", "*/admin")
    assert config._match_pattern("/admin", "*/admin")
    assert not config._match_pattern("/admin/users", "*/admin")

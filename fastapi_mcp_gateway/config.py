"""Configuration module for fastapi-mcp-gateway."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class ExecutionMode(str, Enum):
    """Execution mode for the MCP server."""

    IN_PROCESS = "in_process"  # Call FastAPI app directly
    HTTP = "http"  # Make HTTP requests to a running server
    GRAPHQL = "graphql"  # Execute GraphQL operations


class GraphQLOperationFilter(str, Enum):
    """Filter for GraphQL operations to expose."""

    ALL = "all"  # Include both queries and mutations
    QUERIES_ONLY = "queries_only"  # Include only queries
    MUTATIONS_ONLY = "mutations_only"  # Include only mutations


@dataclass
class GatewayConfig:
    """Configuration for the MCP gateway.

    Attributes:
        mode: Execution mode (in_process, http, or graphql)
        base_url: Base URL for HTTP mode (e.g., "http://localhost:8000")
        include_paths: List of path patterns to include (None = all)
        exclude_paths: List of path patterns to exclude
        auth_factory: Optional callable that returns auth headers/credentials
        log_level: Logging level for the gateway
        timeout: HTTP request timeout in seconds
        max_retries: Maximum number of HTTP request retries
        graphql_endpoint: GraphQL endpoint path (default: "/graphql")
        graphql_operation_filter: Filter for GraphQL operations
        include_operations: List of operation names to include (GraphQL, None = all)
        exclude_operations: List of operation names to exclude (GraphQL)
    """

    mode: ExecutionMode = ExecutionMode.IN_PROCESS
    base_url: Optional[str] = None
    include_paths: Optional[list[str]] = None
    exclude_paths: list[str] = field(default_factory=list)
    auth_factory: Optional[Callable[[], dict[str, Any]]] = None
    log_level: int = logging.INFO
    timeout: float = 30.0
    max_retries: int = 3
    graphql_endpoint: str = "/graphql"
    graphql_operation_filter: GraphQLOperationFilter = GraphQLOperationFilter.ALL
    include_operations: Optional[list[str]] = None
    exclude_operations: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.mode == ExecutionMode.HTTP and not self.base_url:
            raise ValueError("base_url is required when mode is HTTP")

        if self.mode == ExecutionMode.GRAPHQL and not self.base_url:
            raise ValueError("base_url is required when mode is GRAPHQL")

        if self.mode == ExecutionMode.IN_PROCESS and self.base_url:
            logging.warning(
                "base_url is set but mode is IN_PROCESS. "
                "The base_url will be ignored in in-process mode."
            )

    def should_include_operation(self, operation_name: str) -> bool:
        """Check if a GraphQL operation should be included.

        Args:
            operation_name: The operation name to check

        Returns:
            True if the operation should be included, False otherwise
        """
        # Check exclude list first
        if operation_name in self.exclude_operations:
            return False

        # If include_operations is None, include everything (except excluded)
        if self.include_operations is None:
            return True

        # Check include list
        return operation_name in self.include_operations

    def should_include_path(self, path: str) -> bool:
        """Check if a path should be included based on include/exclude patterns.

        Args:
            path: The API path to check

        Returns:
            True if the path should be included, False otherwise
        """
        # Check exclude patterns first
        for exclude_pattern in self.exclude_paths:
            if self._match_pattern(path, exclude_pattern):
                return False

        # If include_paths is None, include everything (except excluded)
        if self.include_paths is None:
            return True

        # Check include patterns
        for include_pattern in self.include_paths:
            if self._match_pattern(path, include_pattern):
                return True

        return False

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        """Simple pattern matching for paths.

        Supports:
        - Exact match: "/users"
        - Prefix match: "/api/*"
        - Wildcard: "*/admin"

        Args:
            path: The path to check
            pattern: The pattern to match against

        Returns:
            True if the path matches the pattern
        """
        if pattern == path:
            return True

        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return path.startswith(prefix)

        if pattern.startswith("*"):
            suffix = pattern[1:]
            return path.endswith(suffix)

        return False

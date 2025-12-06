"""Execution module for GraphQL operations."""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class GraphQLExecutor:
    """Executes GraphQL operations by making requests to a GraphQL endpoint."""

    def __init__(
        self,
        endpoint_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        auth_factory: Optional[Any] = None,
    ):
        """Initialize the GraphQL executor.

        Args:
            endpoint_url: GraphQL endpoint URL
            timeout: HTTP request timeout
            max_retries: Maximum retries for HTTP requests
            auth_factory: Optional callable that returns auth headers
        """
        self.endpoint_url = endpoint_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth_factory = auth_factory

        logger.info(f"GraphQLExecutor initialized with endpoint: {endpoint_url}")

    async def execute_operation(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        operation_name: Optional[str] = None,
    ) -> Any:
        """Execute a GraphQL operation.

        Args:
            query: GraphQL query or mutation string
            variables: Optional variables for the operation
            operation_name: Optional operation name

        Returns:
            Response data from the GraphQL server

        Raises:
            Exception: If the execution fails
        """
        logger.debug(
            f"Executing GraphQL operation: {operation_name or 'unnamed'}\n"
            f"Query: {query}\n"
            f"Variables: {variables}"
        )

        # Prepare the request payload
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.auth_factory:
            auth_data = self.auth_factory()
            if isinstance(auth_data, dict):
                headers.update(auth_data)

        # Execute the request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    self.endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

                # Check for GraphQL errors
                if "errors" in result:
                    error_messages = [
                        err.get("message", str(err)) for err in result["errors"]
                    ]
                    logger.error(f"GraphQL errors: {error_messages}")
                    raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

                # Extract data
                if "data" in result:
                    return result["data"]
                else:
                    logger.warning("GraphQL response has no data field")
                    return result

            except httpx.HTTPError as e:
                logger.error(f"HTTP error during GraphQL execution: {e}")
                raise

    async def execute_tool(
        self,
        tool_metadata: dict[str, Any],
        arguments: dict[str, Any],
    ) -> Any:
        """Execute a GraphQL tool call.

        Args:
            tool_metadata: Tool metadata containing operation details
            arguments: Tool arguments

        Returns:
            Response from the GraphQL server

        Raises:
            Exception: If the execution fails
        """
        from fastapi_mcp_gateway.graphql_mapping import GraphQLOperationMapper

        operation_type = tool_metadata["operation_type"]
        operation_name = tool_metadata["operation_name"]
        field_definition = tool_metadata["field"]

        # Build the GraphQL query
        query, variables = GraphQLOperationMapper.build_query_string(
            operation_name,
            operation_type,
            arguments,
            field_definition,
        )

        # Execute the operation
        result = await self.execute_operation(
            query=query,
            variables=variables,
            operation_name=operation_name,
        )

        # Extract the specific operation result
        if isinstance(result, dict) and operation_name in result:
            return result[operation_name]

        return result

    async def introspect_schema(self) -> dict[str, Any]:
        """Introspect the GraphQL schema.

        Returns:
            Introspection result

        Raises:
            Exception: If introspection fails
        """
        from fastapi_mcp_gateway.graphql_loader import INTROSPECTION_QUERY

        logger.info("Introspecting GraphQL schema")
        result = await self.execute_operation(INTROSPECTION_QUERY)

        if "__schema" in result:
            return result["__schema"]

        raise Exception("Invalid introspection result")

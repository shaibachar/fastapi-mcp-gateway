"""MCP server implementation."""

import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from fastapi_mcp_gateway.config import ExecutionMode, GatewayConfig
from fastapi_mcp_gateway.execution import ToolExecutor
from fastapi_mcp_gateway.mapping import OperationMapper
from fastapi_mcp_gateway.openapi_loader import OpenAPILoader

logger = logging.getLogger(__name__)


class MCPGatewayServer:
    """MCP server that exposes REST API endpoints as tools."""

    def __init__(
        self,
        schema: dict[str, Any],
        config: Optional[GatewayConfig] = None,
        fastapi_app: Optional[Any] = None,
    ):
        """Initialize the MCP gateway server.

        Args:
            schema: OpenAPI schema
            config: Gateway configuration
            fastapi_app: Optional FastAPI app for in-process mode
        """
        self.schema = schema
        self.config = config or GatewayConfig()
        self.fastapi_app = fastapi_app

        # Validate schema
        OpenAPILoader.validate_schema(schema)

        # Set up logging
        logging.basicConfig(level=self.config.log_level)

        # Map operations to tools
        self.tools = self._create_tools()

        # Create executor
        self.executor = ToolExecutor(
            base_url=self.config.base_url,
            fastapi_app=fastapi_app,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            auth_factory=self.config.auth_factory,
        )

        # Create MCP server
        self.server = Server("fastapi-mcp-gateway")
        self._register_handlers()

        logger.info(f"MCPGatewayServer initialized with {len(self.tools)} tools")

    def _create_tools(self) -> list[dict[str, Any]]:
        """Create MCP tools from OpenAPI schema.

        Returns:
            List of tool definitions
        """
        all_tools = OperationMapper.map_openapi_to_tools(self.schema)

        # Filter tools based on config
        filtered_tools = [
            tool
            for tool in all_tools
            if self.config.should_include_path(tool["_metadata"]["path"])
        ]

        logger.info(
            f"Created {len(filtered_tools)} tools "
            f"(filtered from {len(all_tools)} total operations)"
        )

        return filtered_tools

    def _register_handlers(self) -> None:
        """Register MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                )
                for tool in self.tools
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Call a tool by name.

            Args:
                name: Tool name
                arguments: Tool arguments

            Returns:
                List of text content with the result
            """
            logger.info(f"Tool call: {name} with arguments: {arguments}")

            # Find the tool
            tool = next((t for t in self.tools if t["name"] == name), None)
            if not tool:
                raise ValueError(f"Tool not found: {name}")

            # Execute the tool
            try:
                result = await self.executor.execute_tool(
                    tool["_metadata"], arguments
                )

                # Convert result to string for MCP
                import json
                result_str = json.dumps(result, indent=2)

                return [
                    TextContent(
                        type="text",
                        text=result_str,
                    )
                ]
            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                return [
                    TextContent(
                        type="text",
                        text=f"Error executing tool: {str(e)}",
                    )
                ]

    async def run(self) -> None:
        """Run the MCP server using stdio transport."""
        logger.info("Starting MCP server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )


def create_mcp_server_from_fastapi(
    app: Any,
    config: Optional[GatewayConfig] = None,
) -> MCPGatewayServer:
    """Create an MCP server from a FastAPI application.

    Args:
        app: FastAPI application instance
        config: Optional gateway configuration

    Returns:
        MCPGatewayServer instance

    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_mcp_gateway import create_mcp_server_from_fastapi

        app = FastAPI()

        @app.get("/users")
        def get_users():
            return [{"id": 1, "name": "Alice"}]

        mcp_server = create_mcp_server_from_fastapi(app)
        await mcp_server.run()
        ```
    """
    # Load schema from FastAPI app
    schema = OpenAPILoader.load_from_fastapi(app)

    # Create config if not provided, ensuring in-process mode
    if config is None:
        config = GatewayConfig(mode=ExecutionMode.IN_PROCESS)
    
    return MCPGatewayServer(schema=schema, config=config, fastapi_app=app)


async def create_mcp_server_from_openapi(
    openapi_url: str,
    config: Optional[GatewayConfig] = None,
) -> MCPGatewayServer:
    """Create an MCP server from an OpenAPI schema URL.

    Args:
        openapi_url: URL to the OpenAPI schema
        config: Optional gateway configuration

    Returns:
        MCPGatewayServer instance

    Example:
        ```python
        from fastapi_mcp_gateway import create_mcp_server_from_openapi

        mcp_server = await create_mcp_server_from_openapi(
            "http://localhost:8000/openapi.json"
        )
        await mcp_server.run()
        ```
    """
    # Load schema from URL
    schema = await OpenAPILoader.load_from_url(openapi_url)

    # Create config if not provided, ensuring HTTP mode
    if config is None:
        # Extract base URL from openapi_url
        base_url = openapi_url.rsplit("/", 1)[0]
        config = GatewayConfig(mode=ExecutionMode.HTTP, base_url=base_url)
    
    return MCPGatewayServer(schema=schema, config=config)

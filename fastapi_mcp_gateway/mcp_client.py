"""MCP client wrapper for calling tools."""

import logging
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Client wrapper for calling MCP tools.

    This provides a simple interface to connect to an MCP server
    and call tools programmatically.
    """

    def __init__(self, server_params: Optional[StdioServerParameters] = None):
        """Initialize the MCP client.

        Args:
            server_params: Optional server parameters for stdio connection
        """
        self.server_params = server_params
        self.session: Optional[ClientSession] = None
        self._connected = False

    async def connect(
        self,
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> None:
        """Connect to an MCP server.

        Args:
            command: Command to run the MCP server
            args: Arguments for the command
            env: Environment variables

        Example:
            ```python
            client = MCPClient()
            await client.connect(
                command="python",
                args=["server.py"]
            )
            ```
        """
        if self._connected:
            logger.warning("Client already connected")
            return

        # Create server params if not provided
        if self.server_params is None:
            if command is None:
                raise ValueError("Either server_params or command must be provided")
            
            self.server_params = StdioServerParameters(
                command=command,
                args=args or [],
                env=env,
            )

        # Connect to the server
        logger.info(f"Connecting to MCP server: {self.server_params.command}")
        
        self.stdio_transport = await stdio_client(self.server_params)
        self.session = ClientSession(
            self.stdio_transport.read,
            self.stdio_transport.write,
        )
        
        await self.session.initialize()
        self._connected = True
        logger.info("Connected to MCP server")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        logger.info("Disconnecting from MCP server")
        if self.session:
            await self.session.__aexit__(None, None, None)
        self._connected = False

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the server.

        Returns:
            List of tool definitions

        Raises:
            RuntimeError: If not connected to a server
        """
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        logger.debug("Listing tools from server")
        result = await self.session.list_tools()
        
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in result.tools
        ]
        
        logger.info(f"Found {len(tools)} tools")
        return tools

    async def call_tool(self, name: str, arguments: Optional[dict[str, Any]] = None) -> Any:
        """Call a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments (default: empty dict)

        Returns:
            Tool result

        Raises:
            RuntimeError: If not connected to a server

        Example:
            ```python
            result = await client.call_tool(
                "get_users",
                {"page": 1, "limit": 10}
            )
            ```
        """
        if not self._connected or not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        arguments = arguments or {}
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        result = await self.session.call_tool(name, arguments)
        
        # Extract text content from result
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, "text"):
                # Try to parse as JSON
                import json
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text
            return str(content)
        
        return None

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()


async def create_client(
    command: str,
    args: Optional[list[str]] = None,
    env: Optional[dict[str, str]] = None,
) -> MCPClient:
    """Create and connect an MCP client.

    Args:
        command: Command to run the MCP server
        args: Arguments for the command
        env: Environment variables

    Returns:
        Connected MCPClient instance

    Example:
        ```python
        client = await create_client(
            command="python",
            args=["server.py"]
        )
        
        tools = await client.list_tools()
        result = await client.call_tool("get_users", {"page": 1})
        
        await client.disconnect()
        ```
    """
    client = MCPClient()
    await client.connect(command=command, args=args, env=env)
    return client

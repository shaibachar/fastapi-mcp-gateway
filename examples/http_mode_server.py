"""Example showing HTTP mode with an external API."""

import asyncio
from fastapi_mcp_gateway import create_mcp_server_from_openapi
from fastapi_mcp_gateway.config import GatewayConfig, ExecutionMode


async def main():
    """Run MCP server in HTTP mode connecting to an external API."""
    
    # Configuration for HTTP mode
    config = GatewayConfig(
        mode=ExecutionMode.HTTP,
        base_url="http://localhost:8000",
        # Only expose /users endpoints
        include_paths=["/users*"],
    )
    
    print("Loading OpenAPI schema from http://localhost:8000/openapi.json")
    print("Make sure your FastAPI server is running on port 8000!")
    
    # Create MCP server from external API
    mcp_server = await create_mcp_server_from_openapi(
        "http://localhost:8000/openapi.json",
        config=config
    )
    
    print(f"Starting MCP server in HTTP mode...")
    print(f"Exposing {len(mcp_server.tools)} tools from the API")
    
    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())

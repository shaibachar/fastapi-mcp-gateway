"""Example MCP server that exposes a GraphQL API."""

import asyncio

from fastapi_mcp_gateway import create_mcp_server_from_graphql
from fastapi_mcp_gateway.config import GatewayConfig, GraphQLOperationFilter


async def main():
    """Run MCP server for GraphQL endpoint."""

    print("Make sure the GraphQL server is running first!")
    print("Run: python examples/graphql_server.py")
    print()

    # Create MCP server from GraphQL endpoint
    config = GatewayConfig(
        # Include both queries and mutations
        graphql_operation_filter=GraphQLOperationFilter.ALL,
        # You can also filter specific operations:
        # include_operations=["user", "users", "createUser"],
    )

    mcp_server = await create_mcp_server_from_graphql(
        "http://localhost:8000/graphql",
        config=config,
    )

    print(f"Starting MCP server with {len(mcp_server.tools)} GraphQL tools...")
    print("Available tools:")
    for tool in mcp_server.tools:
        op_type = tool["_metadata"]["operation_type"]
        print(f"  - {tool['name']} ({op_type}): {tool['description']}")
    print()

    await mcp_server.run()


if __name__ == "__main__":
    asyncio.run(main())

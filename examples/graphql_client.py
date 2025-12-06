"""Example MCP client for GraphQL server."""

import asyncio
from fastapi_mcp_gateway import MCPClient


async def main():
    """Demonstrate GraphQL MCP client usage."""

    # Create and connect client
    client = MCPClient()

    print("Connecting to GraphQL MCP server...")
    await client.connect(
        command="python",
        args=["examples/graphql_mcp_server.py"],
    )

    try:
        # List available tools
        print("\nListing available tools...")
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

        # Query: Get a specific user
        print("\n--- Calling GraphQL query: user ---")
        user = await client.call_tool("user", {"id": 1})
        print(f"User: {user}")

        # Query: Get all users
        print("\n--- Calling GraphQL query: users ---")
        users = await client.call_tool("users", {})
        print(f"Users: {users}")

        # Mutation: Create a user
        print("\n--- Calling GraphQL mutation: createUser ---")
        new_user = await client.call_tool(
            "createuser",
            {"name": "Charlie", "email": "charlie@example.com"},
        )
        print(f"Created user: {new_user}")

        # Mutation: Update a user
        print("\n--- Calling GraphQL mutation: updateUser ---")
        updated_user = await client.call_tool(
            "updateuser",
            {"id": 1, "name": "Alice Updated", "email": "alice.new@example.com"},
        )
        print(f"Updated user: {updated_user}")

    finally:
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

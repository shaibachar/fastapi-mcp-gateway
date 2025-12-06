"""Example MCP client for connecting to the simple server."""

import asyncio
from fastapi_mcp_gateway import MCPClient


async def main():
    """Main function demonstrating MCP client usage."""
    # Create and connect client
    client = MCPClient()
    
    print("Connecting to MCP server...")
    await client.connect(
        command="python",
        args=["examples/simple_server.py"]
    )
    
    try:
        # List available tools
        print("\nListing available tools...")
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Get all users
        print("\n--- Calling get_users ---")
        users = await client.call_tool("get_users", {"page": 1, "limit": 10})
        print(f"Users: {users}")
        
        # Get a specific user
        print("\n--- Calling get_users_user_id ---")
        user = await client.call_tool("get_users_user_id", {"user_id": 1})
        print(f"User 1: {user}")
        
        # Create a new user
        print("\n--- Calling post_users ---")
        new_user = await client.call_tool(
            "post_users",
            {
                "name": "Charlie",
                "email": "charlie@example.com"
            }
        )
        print(f"Created user: {new_user}")
        
        # Update a user
        print("\n--- Calling put_users_user_id ---")
        updated_user = await client.call_tool(
            "put_users_user_id",
            {
                "user_id": 1,
                "name": "Alice Updated",
                "email": "alice.updated@example.com"
            }
        )
        print(f"Updated user: {updated_user}")
        
        # Get all users again to see changes
        print("\n--- Final user list ---")
        final_users = await client.call_tool("get_users", {"page": 1, "limit": 10})
        print(f"All users: {final_users}")
        
    finally:
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

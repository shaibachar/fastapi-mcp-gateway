"""Example GraphQL server with MCP gateway using Strawberry."""

import asyncio
from typing import Optional

import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI

from fastapi_mcp_gateway import create_mcp_server_from_graphql
from fastapi_mcp_gateway.config import GatewayConfig, ExecutionMode


# GraphQL Types
@strawberry.type
class User:
    id: int
    name: str
    email: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> Optional[User]:
        """Get a user by ID."""
        # Mock data
        users = {
            1: User(id=1, name="Alice", email="alice@example.com"),
            2: User(id=2, name="Bob", email="bob@example.com"),
        }
        return users.get(id)

    @strawberry.field
    def users(self) -> list[User]:
        """Get all users."""
        return [
            User(id=1, name="Alice", email="alice@example.com"),
            User(id=2, name="Bob", email="bob@example.com"),
        ]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, email: str) -> User:
        """Create a new user."""
        # Mock creation
        return User(id=3, name=name, email=email)

    @strawberry.mutation
    def update_user(self, id: int, name: str, email: str) -> User:
        """Update a user."""
        return User(id=id, name=name, email=email)


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Create FastAPI app with GraphQL endpoint
app = FastAPI(title="GraphQL Example API")
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# Run as a regular FastAPI server
if __name__ == "__main__":
    import uvicorn

    print("Starting GraphQL server on http://localhost:8000/graphql")
    print("You can test it at http://localhost:8000/graphql")
    uvicorn.run(app, host="0.0.0.0", port=8000)

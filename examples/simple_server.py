"""Example FastAPI server with MCP gateway."""

import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fastapi_mcp_gateway import create_mcp_server_from_fastapi
from fastapi_mcp_gateway.config import GatewayConfig, ExecutionMode

# Create FastAPI app
app = FastAPI(
    title="Example API",
    description="A simple example API for demonstrating fastapi-mcp-gateway",
    version="1.0.0"
)

# Data models
class User(BaseModel):
    id: int
    name: str
    email: str

class CreateUserRequest(BaseModel):
    name: str
    email: str

# In-memory database
users_db = [
    User(id=1, name="Alice", email="alice@example.com"),
    User(id=2, name="Bob", email="bob@example.com"),
]

# Routes
@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to the Example API"}

@app.get("/users", response_model=list[User])
def get_users(page: int = 1, limit: int = 10):
    """Get all users with pagination."""
    start = (page - 1) * limit
    end = start + limit
    return users_db[start:end]

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    """Get a specific user by ID."""
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=User)
def create_user(user: CreateUserRequest):
    """Create a new user."""
    new_id = max(u.id for u in users_db) + 1 if users_db else 1
    new_user = User(id=new_id, name=user.name, email=user.email)
    users_db.append(new_user)
    return new_user

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: CreateUserRequest):
    """Update a user."""
    existing_user = next((u for u in users_db if u.id == user_id), None)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_user.name = user.name
    existing_user.email = user.email
    return existing_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user."""
    global users_db
    users_db = [u for u in users_db if u.id != user_id]
    return {"message": "User deleted"}

# MCP server setup
async def run_mcp_server():
    """Run the MCP server."""
    config = GatewayConfig(
        mode=ExecutionMode.IN_PROCESS,
        # Exclude the root endpoint
        exclude_paths=["/"],
    )
    
    mcp_server = create_mcp_server_from_fastapi(app, config=config)
    print("Starting MCP server...")
    print(f"Exposing {len(mcp_server.tools)} tools from the API")
    
    await mcp_server.run()

if __name__ == "__main__":
    # Run the MCP server
    asyncio.run(run_mcp_server())

# Examples

This directory contains example code demonstrating various use cases of fastapi-mcp-gateway.

## Files

### `simple_server.py`

A complete example showing:
- Creating a FastAPI app with multiple endpoints
- Converting it to an MCP server
- Running the MCP server in IN_PROCESS mode

Run it:
```bash
python examples/simple_server.py
```

### `simple_client.py`

Example MCP client that connects to the simple server and demonstrates:
- Connecting to an MCP server
- Listing available tools
- Calling various tools (GET, POST, PUT)

Run it (in a separate terminal from the server):
```bash
python examples/simple_client.py
```

### `http_mode_server.py`

Example showing HTTP mode:
- Connecting to an external FastAPI server
- Loading OpenAPI schema from a URL
- Making HTTP requests to execute tools

To use this example:
1. First, run a FastAPI server on port 8000 (you can use uvicorn with simple_server.py)
2. Then run this example

```bash
# Terminal 1: Run FastAPI server
uvicorn examples.simple_server:app --port 8000

# Terminal 2: Run MCP server in HTTP mode
python examples/http_mode_server.py
```

## Tips

- The MCP server runs on stdio, so you'll see MCP protocol messages in the output
- Use the client examples to see how to programmatically interact with the server
- Modify the configurations to experiment with path filtering and other options

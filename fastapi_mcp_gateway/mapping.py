"""Mapping layer to convert OpenAPI operations to MCP tool definitions."""

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


class OperationMapper:
    """Maps OpenAPI operations to MCP tool definitions."""

    HTTP_METHODS = ["get", "post", "put", "patch", "delete", "head", "options"]

    @staticmethod
    def generate_tool_name(
        method: str, path: str, operation_id: Optional[str] = None
    ) -> str:
        """Generate a tool name from the operation.

        Priority:
        1. Use operationId if available
        2. Generate from method + path

        Args:
            method: HTTP method (get, post, etc.)
            path: API path (e.g., /users/{id})
            operation_id: Optional operationId from OpenAPI

        Returns:
            Tool name suitable for MCP
        """
        if operation_id:
            # Clean up operationId to be MCP-friendly
            name = re.sub(r"[^a-zA-Z0-9_]", "_", operation_id)
            return name.lower()

        # Generate from method + path
        # Convert /users/{id} to get_users_id
        clean_path = re.sub(r"[{}]", "", path)  # Remove braces
        clean_path = re.sub(r"[^a-zA-Z0-9/]", "_", clean_path)  # Replace special chars
        clean_path = clean_path.strip("/").replace("/", "_")  # Convert slashes
        
        tool_name = f"{method.lower()}_{clean_path}".lower()
        # Remove consecutive underscores
        tool_name = re.sub(r"_+", "_", tool_name)
        
        return tool_name

    @staticmethod
    def extract_description(operation: dict[str, Any]) -> str:
        """Extract description from operation.

        Combines summary and description if both are present.

        Args:
            operation: OpenAPI operation object

        Returns:
            Combined description
        """
        summary = operation.get("summary", "")
        description = operation.get("description", "")

        if summary and description:
            return f"{summary}. {description}"
        elif summary:
            return summary
        elif description:
            return description
        else:
            return "No description available"

    @staticmethod
    def extract_parameters(
        operation: dict[str, Any], path: str
    ) -> dict[str, Any]:
        """Extract and merge parameters from path, query, header, and body.

        Args:
            operation: OpenAPI operation object
            path: API path (for extracting path parameters)

        Returns:
            JSON schema for tool input parameters
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        # Extract path parameters
        path_params = re.findall(r"\{([^}]+)\}", path)
        for param in path_params:
            properties[param] = {
                "type": "string",
                "description": f"Path parameter: {param}",
            }
            required.append(param)

        # Extract parameters from the operation
        parameters = operation.get("parameters", [])
        for param in parameters:
            param_name = param.get("name")
            param_in = param.get("in")  # query, header, path, cookie
            param_schema = param.get("schema", {})
            param_required = param.get("required", False)

            if param_name:
                properties[param_name] = {
                    "type": param_schema.get("type", "string"),
                    "description": param.get("description", f"{param_in} parameter: {param_name}"),
                }

                # Add additional schema properties if present
                for key in ["enum", "default", "minimum", "maximum", "pattern"]:
                    if key in param_schema:
                        properties[param_name][key] = param_schema[key]

                if param_required and param_name not in required:
                    required.append(param_name)

        # Extract request body (for POST, PUT, PATCH)
        request_body = operation.get("requestBody")
        if request_body:
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            body_schema = json_content.get("schema", {})

            # If body has properties, merge them
            if "properties" in body_schema:
                for prop_name, prop_schema in body_schema["properties"].items():
                    properties[prop_name] = prop_schema

                # Add required fields from body
                body_required = body_schema.get("required", [])
                required.extend([r for r in body_required if r not in required])
            else:
                # If no properties, treat the whole body as a single parameter
                properties["body"] = body_schema
                if request_body.get("required", False):
                    required.append("body")

        # Build the input schema
        input_schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            input_schema["required"] = required

        return input_schema

    @staticmethod
    def extract_response_schema(operation: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Extract the response schema for successful responses.

        Looks for 200/201 responses with JSON content.

        Args:
            operation: OpenAPI operation object

        Returns:
            JSON schema for the response, or None if not available
        """
        responses = operation.get("responses", {})

        # Try common success status codes
        for status_code in ["200", "201", "204"]:
            response = responses.get(status_code)
            if response:
                content = response.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema")
                if schema:
                    return schema

        return None

    @classmethod
    def map_operation_to_tool(
        cls,
        method: str,
        path: str,
        operation: dict[str, Any],
    ) -> dict[str, Any]:
        """Map an OpenAPI operation to an MCP tool definition.

        Args:
            method: HTTP method
            path: API path
            operation: OpenAPI operation object

        Returns:
            MCP tool definition
        """
        tool_name = cls.generate_tool_name(
            method, path, operation.get("operationId")
        )
        description = cls.extract_description(operation)
        input_schema = cls.extract_parameters(operation, path)

        tool_def = {
            "name": tool_name,
            "description": description,
            "inputSchema": input_schema,
        }

        logger.debug(f"Mapped {method.upper()} {path} -> tool '{tool_name}'")
        return tool_def

    @classmethod
    def map_openapi_to_tools(
        cls, schema: dict[str, Any], include_paths: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Map all operations in an OpenAPI schema to MCP tools.

        Args:
            schema: OpenAPI schema
            include_paths: Optional list of paths to include (None = all)

        Returns:
            List of MCP tool definitions
        """
        tools = []
        paths = schema.get("paths", {})

        for path, path_item in paths.items():
            # Check if path should be included
            if include_paths and path not in include_paths:
                continue

            for method in cls.HTTP_METHODS:
                operation = path_item.get(method)
                if operation:
                    tool = cls.map_operation_to_tool(method, path, operation)
                    # Store metadata for execution
                    tool["_metadata"] = {
                        "method": method.upper(),
                        "path": path,
                        "operation": operation,
                    }
                    tools.append(tool)

        logger.info(f"Mapped {len(tools)} operations to MCP tools")
        return tools

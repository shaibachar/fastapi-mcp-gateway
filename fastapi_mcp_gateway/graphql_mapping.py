"""Mapping layer to convert GraphQL operations to MCP tool definitions."""

import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GraphQLOperationMapper:
    """Maps GraphQL operations (queries/mutations) to MCP tool definitions."""

    @staticmethod
    def generate_tool_name(operation_name: str, operation_type: str = "query") -> str:
        """Generate a tool name from the GraphQL operation.

        Args:
            operation_name: Name of the query or mutation
            operation_type: Type of operation (query or mutation)

        Returns:
            Tool name suitable for MCP
        """
        # Clean up operation name to be MCP-friendly
        name = re.sub(r"[^a-zA-Z0-9_]", "_", operation_name)
        return name.lower()

    @staticmethod
    def extract_description(field: dict[str, Any]) -> str:
        """Extract description from a GraphQL field.

        Args:
            field: GraphQL field definition

        Returns:
            Description string
        """
        description = field.get("description", "")
        if description:
            return description
        
        # Fallback: generate from name
        name = field.get("name", "unknown")
        return f"GraphQL operation: {name}"

    @staticmethod
    def extract_type_name(type_ref: dict[str, Any]) -> str:
        """Extract the actual type name from a type reference.

        GraphQL types can be nested (e.g., NON_NULL -> LIST -> NON_NULL -> SCALAR)
        This unwraps to get the actual type name.

        Args:
            type_ref: GraphQL type reference

        Returns:
            Type name as a string
        """
        if not type_ref:
            return "String"

        # Unwrap NON_NULL and LIST wrappers
        current = type_ref
        while current and current.get("kind") in ["NON_NULL", "LIST"]:
            current = current.get("ofType")

        if current and current.get("name"):
            return current["name"]

        return "String"

    @staticmethod
    def graphql_type_to_json_schema_type(graphql_type: str) -> str:
        """Convert GraphQL type to JSON Schema type.

        Args:
            graphql_type: GraphQL type name

        Returns:
            JSON Schema type
        """
        type_mapping = {
            "String": "string",
            "Int": "integer",
            "Float": "number",
            "Boolean": "boolean",
            "ID": "string",
        }
        return type_mapping.get(graphql_type, "string")

    @staticmethod
    def is_required(type_ref: dict[str, Any]) -> bool:
        """Check if a GraphQL type is required (NON_NULL).

        Args:
            type_ref: GraphQL type reference

        Returns:
            True if the type is NON_NULL
        """
        return type_ref.get("kind") == "NON_NULL"

    @staticmethod
    def extract_arguments(field: dict[str, Any]) -> dict[str, Any]:
        """Extract arguments from a GraphQL field to create input schema.

        Args:
            field: GraphQL field definition

        Returns:
            JSON schema for tool input parameters
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        args = field.get("args", [])
        for arg in args:
            arg_name = arg.get("name")
            arg_type = arg.get("type", {})
            
            if not arg_name:
                continue

            # Check if required
            if GraphQLOperationMapper.is_required(arg_type):
                required.append(arg_name)

            # Extract type name
            type_name = GraphQLOperationMapper.extract_type_name(arg_type)
            json_type = GraphQLOperationMapper.graphql_type_to_json_schema_type(type_name)

            properties[arg_name] = {
                "type": json_type,
                "description": arg.get("description", f"Argument: {arg_name}"),
            }

            # Add default value if present
            default_value = arg.get("defaultValue")
            if default_value is not None:
                properties[arg_name]["default"] = default_value

        # Build the input schema
        input_schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            input_schema["required"] = required

        return input_schema

    @staticmethod
    def map_operation_to_tool(
        field: dict[str, Any],
        operation_type: str = "query",
    ) -> dict[str, Any]:
        """Map a GraphQL operation (query or mutation) to an MCP tool definition.

        Args:
            field: GraphQL field definition
            operation_type: Type of operation ("query" or "mutation")

        Returns:
            MCP tool definition
        """
        operation_name = field.get("name", "unknown")
        tool_name = GraphQLOperationMapper.generate_tool_name(
            operation_name, operation_type
        )
        description = GraphQLOperationMapper.extract_description(field)
        input_schema = GraphQLOperationMapper.extract_arguments(field)

        tool_def = {
            "name": tool_name,
            "description": f"[{operation_type.upper()}] {description}",
            "inputSchema": input_schema,
        }

        logger.debug(f"Mapped GraphQL {operation_type} '{operation_name}' -> tool '{tool_name}'")
        return tool_def

    @classmethod
    def map_graphql_to_tools(
        cls,
        schema: dict[str, Any],
        include_queries: bool = True,
        include_mutations: bool = True,
    ) -> list[dict[str, Any]]:
        """Map all GraphQL operations in a schema to MCP tools.

        Args:
            schema: GraphQL introspection schema
            include_queries: Whether to include queries
            include_mutations: Whether to include mutations

        Returns:
            List of MCP tool definitions
        """
        from fastapi_mcp_gateway.graphql_loader import GraphQLLoader

        tools = []

        # Map queries
        if include_queries:
            queries = GraphQLLoader.get_queries(schema)
            for query_field in queries:
                tool = cls.map_operation_to_tool(query_field, "query")
                # Store metadata for execution
                tool["_metadata"] = {
                    "operation_type": "query",
                    "operation_name": query_field.get("name"),
                    "field": query_field,
                }
                tools.append(tool)

        # Map mutations
        if include_mutations:
            mutations = GraphQLLoader.get_mutations(schema)
            for mutation_field in mutations:
                tool = cls.map_operation_to_tool(mutation_field, "mutation")
                # Store metadata for execution
                tool["_metadata"] = {
                    "operation_type": "mutation",
                    "operation_name": mutation_field.get("name"),
                    "field": mutation_field,
                }
                tools.append(tool)

        logger.info(
            f"Mapped {len(tools)} GraphQL operations to MCP tools "
            f"({sum(1 for t in tools if t['_metadata']['operation_type'] == 'query')} queries, "
            f"{sum(1 for t in tools if t['_metadata']['operation_type'] == 'mutation')} mutations)"
        )

        return tools

    @staticmethod
    def build_query_string(
        operation_name: str,
        operation_type: str,
        arguments: dict[str, Any],
        field_definition: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Build a GraphQL query string from operation details.

        Args:
            operation_name: Name of the operation
            operation_type: "query" or "mutation"
            arguments: Arguments to pass to the operation
            field_definition: GraphQL field definition

        Returns:
            Tuple of (query_string, variables_dict)
        """
        # Build variables declaration
        args = field_definition.get("args", [])
        var_declarations = []
        variables = {}

        for arg in args:
            arg_name = arg.get("name")
            if arg_name in arguments:
                # Simplified type handling
                arg_type = arg.get("type", {})
                type_name = GraphQLOperationMapper.extract_type_name(arg_type)
                is_required = GraphQLOperationMapper.is_required(arg_type)
                
                type_str = type_name
                if is_required:
                    type_str += "!"
                
                var_declarations.append(f"${arg_name}: {type_str}")
                variables[arg_name] = arguments[arg_name]

        # Build the query
        vars_part = f"({', '.join(var_declarations)})" if var_declarations else ""
        args_part = ", ".join([f"{k}: ${k}" for k in variables.keys()])
        args_part = f"({args_part})" if args_part else ""

        # Simple field selection (just return all scalar fields)
        # In a full implementation, this would be more sophisticated
        query = f"""
{operation_type} {vars_part} {{
  {operation_name}{args_part}
}}
""".strip()

        return query, variables

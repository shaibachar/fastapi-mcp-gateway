"""GraphQL schema loader and introspection."""

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


# GraphQL introspection query
INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: false) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
  }
  inputFields {
    ...InputValue
  }
  enumValues(includeDeprecated: false) {
    name
    description
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


class GraphQLLoader:
    """Loads and parses GraphQL schemas from various sources."""

    @staticmethod
    async def load_from_url(
        url: str, timeout: float = 30.0, headers: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        """Load GraphQL schema via introspection query.

        Args:
            url: GraphQL endpoint URL (e.g., http://localhost:8000/graphql)
            timeout: Request timeout in seconds
            headers: Optional headers for authentication

        Returns:
            Introspection result as a dictionary

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is invalid
        """
        logger.info(f"Loading GraphQL schema from URL: {url}")

        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json={"query": INTROSPECTION_QUERY},
                headers=request_headers,
            )
            response.raise_for_status()
            result = response.json()

        if "errors" in result:
            raise ValueError(f"GraphQL introspection failed: {result['errors']}")

        if "data" not in result or "__schema" not in result["data"]:
            raise ValueError("Invalid GraphQL introspection response")

        schema = result["data"]["__schema"]
        logger.info(
            f"Loaded GraphQL schema with {len(schema.get('types', []))} types"
        )
        return schema

    @staticmethod
    def load_from_file(file_path: str) -> dict[str, Any]:
        """Load GraphQL schema from a schema definition file (.graphql or .gql).

        Note: This loads the raw schema text. For introspection-style data,
        you'll need to parse it using a GraphQL library.

        Args:
            file_path: Path to the GraphQL schema file

        Returns:
            Schema as a dictionary (simplified representation)

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        logger.info(f"Loading GraphQL schema from file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            schema_text = f.read()

        # For a full implementation, you'd parse this using graphql-core
        # For now, return a simple structure
        logger.warning(
            "File-based schema loading is simplified. "
            "Consider using introspection from a running server."
        )

        return {"schema_text": schema_text}

    @staticmethod
    def load_from_dict(schema: dict[str, Any]) -> dict[str, Any]:
        """Load GraphQL schema from a dictionary (introspection result).

        Args:
            schema: GraphQL introspection schema as a dictionary

        Returns:
            The schema (validated)

        Raises:
            ValueError: If the schema is invalid
        """
        logger.info("Loading GraphQL schema from dictionary")

        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")

        if "types" not in schema:
            raise ValueError("Schema must contain 'types' field")

        logger.info(f"Loaded GraphQL schema with {len(schema['types'])} types")
        return schema

    @staticmethod
    def get_query_type(schema: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Get the Query type from the schema.

        Args:
            schema: GraphQL introspection schema

        Returns:
            Query type definition or None
        """
        query_type_name = schema.get("queryType", {}).get("name")
        if not query_type_name:
            return None

        for type_def in schema.get("types", []):
            if type_def.get("name") == query_type_name:
                return type_def

        return None

    @staticmethod
    def get_mutation_type(schema: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Get the Mutation type from the schema.

        Args:
            schema: GraphQL introspection schema

        Returns:
            Mutation type definition or None
        """
        mutation_type_name = schema.get("mutationType", {}).get("name")
        if not mutation_type_name:
            return None

        for type_def in schema.get("types", []):
            if type_def.get("name") == mutation_type_name:
                return type_def

        return None

    @staticmethod
    def get_queries(schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all query operations from the schema.

        Args:
            schema: GraphQL introspection schema

        Returns:
            List of query field definitions
        """
        query_type = GraphQLLoader.get_query_type(schema)
        if not query_type:
            return []

        return query_type.get("fields", [])

    @staticmethod
    def get_mutations(schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all mutation operations from the schema.

        Args:
            schema: GraphQL introspection schema

        Returns:
            List of mutation field definitions
        """
        mutation_type = GraphQLLoader.get_mutation_type(schema)
        if not mutation_type:
            return []

        return mutation_type.get("fields", [])

    @staticmethod
    def get_all_operations(schema: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        """Get all queries and mutations from the schema.

        Args:
            schema: GraphQL introspection schema

        Returns:
            Dictionary with 'queries' and 'mutations' keys
        """
        return {
            "queries": GraphQLLoader.get_queries(schema),
            "mutations": GraphQLLoader.get_mutations(schema),
        }

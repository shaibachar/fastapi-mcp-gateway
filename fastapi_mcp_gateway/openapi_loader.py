"""OpenAPI schema loader and parser."""

import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class OpenAPILoader:
    """Loads and parses OpenAPI schemas from various sources."""

    @staticmethod
    async def load_from_url(url: str, timeout: float = 30.0) -> dict[str, Any]:
        """Load OpenAPI schema from a URL.

        Args:
            url: URL to the OpenAPI schema (e.g., http://localhost:8000/openapi.json)
            timeout: Request timeout in seconds

        Returns:
            Parsed OpenAPI schema as a dictionary

        Raises:
            httpx.HTTPError: If the request fails
            json.JSONDecodeError: If the response is not valid JSON
        """
        logger.info(f"Loading OpenAPI schema from URL: {url}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            schema = response.json()

        logger.info(f"Loaded OpenAPI schema version: {schema.get('openapi', 'unknown')}")
        return schema

    @staticmethod
    def load_from_fastapi(app: Any) -> dict[str, Any]:
        """Load OpenAPI schema from a FastAPI application.

        Args:
            app: FastAPI application instance

        Returns:
            Parsed OpenAPI schema as a dictionary

        Raises:
            AttributeError: If the app doesn't have an openapi method
        """
        logger.info("Loading OpenAPI schema from FastAPI app")

        if not hasattr(app, "openapi"):
            raise AttributeError(
                "Provided app does not have an 'openapi' method. "
                "Is it a FastAPI application?"
            )

        schema = app.openapi()
        logger.info(f"Loaded OpenAPI schema version: {schema.get('openapi', 'unknown')}")
        return schema

    @staticmethod
    def load_from_dict(schema: dict[str, Any]) -> dict[str, Any]:
        """Load OpenAPI schema from a dictionary.

        Args:
            schema: OpenAPI schema as a dictionary

        Returns:
            The schema (validated)

        Raises:
            ValueError: If the schema is invalid
        """
        logger.info("Loading OpenAPI schema from dictionary")

        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")

        if "openapi" not in schema and "swagger" not in schema:
            raise ValueError(
                "Schema must contain 'openapi' or 'swagger' version field"
            )

        logger.info(f"Loaded OpenAPI schema version: {schema.get('openapi', schema.get('swagger'))}")
        return schema

    @staticmethod
    def load_from_file(file_path: str) -> dict[str, Any]:
        """Load OpenAPI schema from a file.

        Args:
            file_path: Path to the OpenAPI schema file (JSON or YAML)

        Returns:
            Parsed OpenAPI schema as a dictionary

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        logger.info(f"Loading OpenAPI schema from file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith((".yaml", ".yml")):
                # Import yaml only if needed
                try:
                    import yaml
                    schema = yaml.safe_load(f)
                except ImportError:
                    raise ImportError(
                        "PyYAML is required to load YAML files. "
                        "Install it with: pip install pyyaml"
                    )
            else:
                schema = json.load(f)

        logger.info(f"Loaded OpenAPI schema version: {schema.get('openapi', 'unknown')}")
        return schema

    @staticmethod
    def validate_schema(schema: dict[str, Any]) -> None:
        """Validate that the schema is a supported OpenAPI schema.

        Args:
            schema: OpenAPI schema to validate

        Raises:
            ValueError: If the schema is invalid or unsupported
        """
        version = schema.get("openapi") or schema.get("swagger")
        
        if not version:
            raise ValueError("Schema must contain 'openapi' or 'swagger' version field")

        # Support OpenAPI 3.x
        if isinstance(version, str) and version.startswith("3."):
            return

        # Warn about Swagger 2.0 (OpenAPI 2.0)
        if version == "2.0":
            logger.warning(
                "Swagger 2.0 detected. Some features may not work as expected. "
                "Consider upgrading to OpenAPI 3.x"
            )
            return

        raise ValueError(
            f"Unsupported OpenAPI/Swagger version: {version}. "
            "Supported versions: 3.0.x, 3.1.x"
        )

    @staticmethod
    def get_paths(schema: dict[str, Any]) -> dict[str, Any]:
        """Extract paths from the OpenAPI schema.

        Args:
            schema: OpenAPI schema

        Returns:
            Dictionary of paths and their operations
        """
        return schema.get("paths", {})

    @staticmethod
    def get_servers(schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract server information from the OpenAPI schema.

        Args:
            schema: OpenAPI schema

        Returns:
            List of server definitions
        """
        return schema.get("servers", [])

    @staticmethod
    def get_base_url(schema: dict[str, Any]) -> Optional[str]:
        """Get the first server URL from the schema.

        Args:
            schema: OpenAPI schema

        Returns:
            Base URL or None if no servers are defined
        """
        servers = OpenAPILoader.get_servers(schema)
        if servers and len(servers) > 0:
            return servers[0].get("url")
        return None

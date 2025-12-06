"""Execution module for calling API endpoints."""

import logging
import re
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes MCP tool calls by invoking API endpoints."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        fastapi_app: Optional[Any] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        auth_factory: Optional[Any] = None,
    ):
        """Initialize the executor.

        Args:
            base_url: Base URL for HTTP mode
            fastapi_app: FastAPI app instance for in-process mode
            timeout: HTTP request timeout
            max_retries: Maximum retries for HTTP requests
            auth_factory: Optional callable that returns auth headers
        """
        self.base_url = base_url
        self.fastapi_app = fastapi_app
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth_factory = auth_factory

        # Determine execution mode
        if fastapi_app is not None:
            self.mode = "in_process"
            logger.info("Executor initialized in IN_PROCESS mode")
        elif base_url is not None:
            self.mode = "http"
            logger.info(f"Executor initialized in HTTP mode (base_url={base_url})")
        else:
            raise ValueError("Either base_url or fastapi_app must be provided")

    async def execute_tool(
        self, tool_metadata: dict[str, Any], arguments: dict[str, Any]
    ) -> Any:
        """Execute a tool call.

        Args:
            tool_metadata: Tool metadata containing method, path, etc.
            arguments: Tool arguments

        Returns:
            Response from the API

        Raises:
            Exception: If the execution fails
        """
        method = tool_metadata["method"]
        path = tool_metadata["path"]

        logger.debug(f"Executing {method} {path} with arguments: {arguments}")

        if self.mode == "in_process":
            return await self._execute_in_process(method, path, arguments)
        else:
            return await self._execute_http(method, path, arguments)

    async def _execute_in_process(
        self, method: str, path: str, arguments: dict[str, Any]
    ) -> Any:
        """Execute a tool call in-process using the FastAPI app.

        Args:
            method: HTTP method
            path: API path
            arguments: Tool arguments

        Returns:
            Response from the API
        """
        from fastapi.testclient import TestClient

        # Create a test client for the FastAPI app
        client = TestClient(self.fastapi_app)

        # Prepare the request
        resolved_path, query_params, body = self._prepare_request(path, arguments)

        try:
            # Make the request
            if method == "GET":
                response = client.get(resolved_path, params=query_params)
            elif method == "POST":
                response = client.post(resolved_path, params=query_params, json=body)
            elif method == "PUT":
                response = client.put(resolved_path, params=query_params, json=body)
            elif method == "PATCH":
                response = client.patch(resolved_path, params=query_params, json=body)
            elif method == "DELETE":
                response = client.delete(resolved_path, params=query_params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            
            # Try to return JSON, fall back to text
            try:
                return response.json()
            except Exception:
                return {"status": response.status_code, "text": response.text}

        except Exception as e:
            logger.error(f"In-process execution failed: {e}")
            raise

    async def _execute_http(
        self, method: str, path: str, arguments: dict[str, Any]
    ) -> Any:
        """Execute a tool call via HTTP.

        Args:
            method: HTTP method
            path: API path
            arguments: Tool arguments

        Returns:
            Response from the API
        """
        # Prepare the request
        resolved_path, query_params, body = self._prepare_request(path, arguments)
        url = f"{self.base_url}{resolved_path}"

        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.auth_factory:
            auth_data = self.auth_factory()
            if isinstance(auth_data, dict):
                headers.update(auth_data)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method == "GET":
                    response = await client.get(url, params=query_params, headers=headers)
                elif method == "POST":
                    response = await client.post(
                        url, params=query_params, json=body, headers=headers
                    )
                elif method == "PUT":
                    response = await client.put(
                        url, params=query_params, json=body, headers=headers
                    )
                elif method == "PATCH":
                    response = await client.patch(
                        url, params=query_params, json=body, headers=headers
                    )
                elif method == "DELETE":
                    response = await client.delete(
                        url, params=query_params, headers=headers
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                
                # Try to return JSON, fall back to text
                try:
                    return response.json()
                except Exception:
                    return {"status": response.status_code, "text": response.text}

            except httpx.HTTPError as e:
                logger.error(f"HTTP execution failed: {e}")
                raise

    def _prepare_request(
        self, path: str, arguments: dict[str, Any]
    ) -> tuple[str, dict[str, Any], Optional[dict[str, Any]]]:
        """Prepare the request by separating path params, query params, and body.

        Args:
            path: API path template (e.g., /users/{id})
            arguments: All arguments from the tool call

        Returns:
            Tuple of (resolved_path, query_params, body)
        """
        # Find path parameters
        path_params = re.findall(r"\{([^}]+)\}", path)
        
        # Resolve path parameters
        resolved_path = path
        remaining_args = dict(arguments)
        
        for param in path_params:
            if param in remaining_args:
                value = remaining_args.pop(param)
                resolved_path = resolved_path.replace(f"{{{param}}}", str(value))

        # Separate query params and body
        # Heuristic: if there's a 'body' key, use it as body
        # Otherwise, for GET/DELETE use all as query params
        # For POST/PUT/PATCH, use remaining as body
        
        body = None
        query_params = {}

        if "body" in remaining_args:
            body = remaining_args.pop("body")
            query_params = remaining_args
        else:
            # For now, put everything in query params for GET
            # and in body for POST/PUT/PATCH
            # This is a simplification - in reality, we'd need to check the OpenAPI spec
            query_params = remaining_args

        return resolved_path, query_params, body

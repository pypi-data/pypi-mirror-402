"""OpenAPI Navigator - Tools for navigating OpenAPI specifications."""

import logging
import time
import json as json_module
from typing import Dict, List, Optional, Any
import requests
from fastmcp import FastMCP
from openapi_navigator.spec_manager import SpecManager

logger = logging.getLogger(__name__)

# Create a global spec manager instance that all tools share
_spec_manager = SpecManager()

# Create the main MCP server instance for CLI tools to find
mcp = FastMCP("openapi-navigator")


# Register all tools
@mcp.tool
def load_spec(file_path: str, spec_id: Optional[str] = None) -> str:
    """
    Load an OpenAPI specification from a local file.

    Args:
        file_path: Absolute path to the OpenAPI spec file (YAML or JSON)
        spec_id: Optional custom identifier for the spec. If not provided, will use 'file:{file_path}'

    Returns:
        The spec ID that was assigned to the loaded specification

    Note:
        File path must be absolute for security reasons.
    """
    try:
        return _spec_manager.load_spec_from_file(file_path, spec_id)
    except Exception as e:
        logger.error(f"Failed to load spec from file: {e}")
        raise


@mcp.tool
def load_spec_from_url(
    url: str, spec_id: Optional[str] = None, verify_ssl: bool = True
) -> str:
    """
    Load an OpenAPI specification from a URL.

    Args:
        url: URL to the OpenAPI spec (YAML or JSON)
        spec_id: Optional custom identifier for the spec. If not provided, will use 'url:{url}'
        verify_ssl: Whether to verify SSL certificates (default: True).
                    Set to False to ignore invalid or self-signed certificates.

    Returns:
        The spec ID that was assigned to the loaded specification
    """
    try:
        return _spec_manager.load_spec_from_url(url, spec_id, verify_ssl)
    except Exception as e:
        logger.error(f"Failed to load spec from URL: {e}")
        raise


@mcp.tool
def unload_spec(spec_id: str) -> str:
    """
    Unload an OpenAPI specification from memory.

    Args:
        spec_id: ID of the loaded spec to unload

    Returns:
        Confirmation message
    """
    success = _spec_manager.unload_spec(spec_id)
    if success:
        return f"Successfully unloaded spec: {spec_id}"
    else:
        return f"Spec not found or already unloaded: {spec_id}"


@mcp.tool
def list_loaded_specs() -> List[str]:
    """
    List all currently loaded OpenAPI specifications.

    Returns:
        List of spec IDs that are currently loaded
    """
    return _spec_manager.list_loaded_specs()


@mcp.tool
def get_endpoint(
    spec_id: str, path: str, method: str, summary_only: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Get the operation definition for a specific endpoint.

    Args:
        spec_id: ID of the loaded spec to query
        path: API path (e.g., '/users/{id}')
        method: HTTP method (e.g., 'GET', 'POST')
        summary_only: If True, return only essential fields to reduce token usage (default: False)

    Returns:
        The operation object from the OpenAPI spec (full or summary), or None if not found
    """
    spec = _spec_manager.get_spec(spec_id)
    if not spec:
        raise ValueError(f"No spec found with ID: {spec_id}")

    endpoint = spec.get_endpoint(path, method.upper())
    if not endpoint:
        return None

    if summary_only:
        # Return only essential information to reduce token usage
        return {
            "summary": endpoint.get("summary", ""),
            "description": endpoint.get("description", ""),
            "operationId": endpoint.get("operationId", ""),
            "tags": endpoint.get("tags", []),
            "parameters": [
                {
                    "name": p.get("name", ""),
                    "in": p.get("in", ""),
                    "required": p.get("required", False),
                    "type": p.get("schema", {}).get("type", p.get("type", "")),
                    "description": p.get("description", ""),
                }
                for p in endpoint.get("parameters", [])
            ],
            "responses": {
                code: {
                    "description": resp.get("description", ""),
                    "content_types": (
                        list(resp.get("content", {}).keys())
                        if "content" in resp
                        else []
                    ),
                }
                for code, resp in endpoint.get("responses", {}).items()
            },
            "requestBody": (
                {
                    "required": endpoint.get("requestBody", {}).get("required", False),
                    "content_types": list(
                        endpoint.get("requestBody", {}).get("content", {}).keys()
                    ),
                }
                if "requestBody" in endpoint
                else None
            ),
        }

    return endpoint


@mcp.tool
def search_endpoints(
    spec_id: str, query: str, limit: int = 50, offset: int = 0
) -> Dict[str, Any]:
    """
    Search endpoints using fuzzy matching across paths, summaries, and operation IDs with pagination.

    To get a full list of all endpoints, use an empty string "" or a very short query like "a" as the search term.
    The search will return all endpoints with a relevance score of 100 when the query is very short.

    Args:
        spec_id: ID of the loaded spec to query
        query: Search query string. Use "" or "a" to get all endpoints.
        limit: Maximum number of results to return (default 50, max 200)
        offset: Number of results to skip for pagination (default 0)

    Returns:
        Dictionary containing:
        - endpoints: List of matching endpoints with relevance scores
        - total: Total number of matches (before pagination)
        - limit: Applied limit
        - offset: Applied offset
        - has_more: Whether there are more results available
    """
    spec = _spec_manager.get_spec(spec_id)
    if not spec:
        raise ValueError(f"No spec found with ID: {spec_id}")

    return spec.search_endpoints(query, limit, offset)


@mcp.tool
def get_schema(spec_id: str, schema_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific schema definition from a loaded OpenAPI specification.

    Args:
        spec_id: ID of the loaded spec to query
        schema_name: Name of the schema to retrieve

    Returns:
        The raw schema object from the OpenAPI spec, or None if not found
    """
    spec = _spec_manager.get_spec(spec_id)
    if not spec:
        raise ValueError(f"No spec found with ID: {spec_id}")

    return spec.get_schema(schema_name)


@mcp.tool
def search_schemas(
    spec_id: str, query: str, limit: int = 50, offset: int = 0
) -> Dict[str, Any]:
    """
    Search schema names using fuzzy matching with pagination.

    To get a full list of all schemas, use an empty string "" or a very short query like "a" as the search term.
    The search will return all schemas with a relevance score of 100 when the query is very short.

    Args:
        spec_id: ID of the loaded spec to query
        query: Search query string. Use "" or "a" to get all schemas.
        limit: Maximum number of results to return (default 50, max 200)
        offset: Number of results to skip for pagination (default 0)

    Returns:
        Dictionary containing:
        - schemas: List of matching schema names with relevance scores
        - total: Total number of matches (before pagination)
        - limit: Applied limit
        - offset: Applied offset
        - has_more: Whether there are more results available
    """
    spec = _spec_manager.get_spec(spec_id)
    if not spec:
        raise ValueError(f"No spec found with ID: {spec_id}")

    return spec.search_schemas(query, limit, offset)


@mcp.tool
def get_spec_metadata(spec_id: str) -> Dict[str, Any]:
    """
    Get comprehensive metadata about a loaded OpenAPI specification.

    This includes information about the spec version, title, description, base path,
    servers, contact info, license, and counts of endpoints and schemas.

    Args:
        spec_id: ID of the loaded spec to query

    Returns:
        Dictionary containing spec metadata including base path and help text
    """
    spec = _spec_manager.get_spec(spec_id)
    if not spec:
        raise ValueError(f"No spec found with ID: {spec_id}")

    return spec.get_spec_metadata()


def _make_api_request_impl(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[str] = None,
    timeout: int = 30,
    spec_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Make a generic REST API request with full control over method, headers, parameters, and body.

    This tool enables direct interaction with REST APIs, complementing the OpenAPI exploration tools
    by allowing you to actually call the endpoints you've discovered.

    Args:
        url: The full URL to make the request to
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS). Defaults to GET.
        headers: Optional dictionary of HTTP headers to include in the request
        params: Optional dictionary of URL parameters to append to the URL
        data: Optional request body data as a string (JSON, XML, form data, etc.)
        timeout: Request timeout in seconds. Defaults to 30.
        spec_id: Optional spec ID to use for default headers. If provided, headers from
                 set_spec_headers will be merged (request headers take precedence).

    Returns:
        Dictionary containing:
        - status_code: HTTP status code
        - headers: Response headers as a dictionary
        - body: Raw response body as string
        - json: Parsed JSON response (if response is valid JSON, otherwise None)
        - url: Final URL after any redirects
        - elapsed_ms: Request duration in milliseconds
        - method: The HTTP method that was used

    Raises:
        ValueError: If the URL is invalid or method is not supported, or spec_id doesn't exist
        ConnectionError: If the request fails due to network issues
        TimeoutError: If the request times out
    """
    # Validate method
    valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    method = method.upper()
    if method not in valid_methods:
        raise ValueError(
            f"Invalid HTTP method: {method}. Must be one of {valid_methods}"
        )

    # Validate URL
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    # Merge headers from spec if spec_id provided
    merged_headers = {}
    if spec_id:
        spec = _spec_manager.get_spec(spec_id)
        if not spec:
            raise ValueError(f"No spec found with ID: {spec_id}")
        # Start with spec's default headers
        merged_headers = spec.get_headers()

    # Override with explicit headers (request headers take precedence)
    if headers:
        merged_headers.update(headers)

    try:
        # Prepare the request
        request_kwargs = {
            "method": method,
            "url": url,
            "timeout": timeout,
        }

        if merged_headers:  # Changed from `if headers:`
            request_kwargs["headers"] = merged_headers

        if params:
            request_kwargs["params"] = params

        if data:
            request_kwargs["data"] = data

        # Make the request and time it
        start_time = time.time()
        logger.info(f"Making {method} request to {url}")

        response = requests.request(**request_kwargs)

        end_time = time.time()
        elapsed_ms = int((end_time - start_time) * 1000)

        # Parse JSON response if possible
        response_json = None
        try:
            if response.text.strip():  # Only try to parse if there's content
                response_json = response.json()
        except (json_module.JSONDecodeError, ValueError):
            # Response is not JSON, that's fine
            pass

        # Build response dictionary
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "json": response_json,
            "url": response.url,
            "elapsed_ms": elapsed_ms,
            "method": method,
        }

        logger.info(
            f"Request completed: {method} {url} -> {response.status_code} ({elapsed_ms}ms)"
        )
        return result

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out: {method} {url}")
        raise TimeoutError(f"Request timed out after {timeout} seconds: {str(e)}")

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {method} {url} - {str(e)}")
        raise ConnectionError(f"Failed to connect to {url}: {str(e)}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {method} {url} - {str(e)}")
        raise Exception(f"Request failed: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error during request: {method} {url} - {str(e)}")
        raise Exception(f"Unexpected error: {str(e)}")


@mcp.tool
def make_api_request(
    url: str,
    method: str = "GET",
    headers: dict = None,
    params: dict = None,
    data: str = None,
    timeout: int = 30,
    spec_id: str = None,
) -> dict:
    """
    Make a generic REST API request with full control over method, headers, parameters, and body.

    This tool enables direct interaction with REST APIs, complementing the OpenAPI exploration tools
    by allowing you to actually call the endpoints you've discovered.

    Args:
        url: The full URL to make the request to
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS). Defaults to GET.
        headers: Dictionary of HTTP headers to include in the request (optional)
        params: Dictionary of URL parameters to append to the URL (optional)
        data: Request body data as a string (JSON, XML, form data, etc.) (optional)
        timeout: Request timeout in seconds. Defaults to 30.
        spec_id: Optional spec ID to automatically apply headers from set_spec_headers.
                 Request headers take precedence over spec headers. (optional)

    Returns:
        Dictionary containing:
        - status_code: HTTP status code
        - headers: Response headers as a dictionary
        - body: Raw response body as string
        - json: Parsed JSON response (if response is valid JSON, otherwise None)
        - url: Final URL after any redirects
        - elapsed_ms: Request duration in milliseconds
        - method: The HTTP method that was used

    Raises:
        ValueError: If the URL is invalid or method is not supported, or spec_id doesn't exist
        ConnectionError: If the request fails due to network issues
        TimeoutError: If the request times out

    Example with spec_id:
        # Load and configure a spec with auth
        load_spec_from_url("https://api.example.com/openapi.json", "my-api")
        set_spec_headers("my-api", {"Authorization": "Bearer token123"})

        # Make requests without repeating auth headers
        make_api_request("https://api.example.com/users", spec_id="my-api")

        # Override specific headers while keeping others from spec
        make_api_request(
            "https://api.example.com/admin",
            spec_id="my-api",
            headers={"X-Admin-Token": "admin456"}
        )
    """
    return _make_api_request_impl(url, method, headers, params, data, timeout, spec_id)


def _set_spec_headers_impl(spec_id: str, headers: dict = None) -> str:
    """
    Internal implementation for setting default headers on a spec.

    Args:
        spec_id: ID of the loaded spec to set headers for
        headers: Dictionary of HTTP headers to use by default

    Returns:
        Confirmation message

    Raises:
        ValueError: If the spec_id doesn't exist
    """
    spec = _spec_manager.get_spec(spec_id)
    if not spec:
        raise ValueError(f"No spec found with ID: {spec_id}")

    if headers is None:
        headers = {}

    spec.set_headers(headers)

    header_count = len(headers)
    if header_count == 0:
        return f"Successfully cleared headers for spec: {spec_id}"
    else:
        return f"Successfully set {header_count} default header(s) for spec: {spec_id}"


@mcp.tool
def set_spec_headers(spec_id: str, headers: dict = None) -> str:
    """
    Set default headers for API requests to a loaded OpenAPI spec.

    This allows you to "mount" authentication or other headers to a spec once,
    rather than passing them on every make_api_request call. When making requests
    with make_api_request, you can reference the spec_id to automatically apply
    these headers.

    Args:
        spec_id: ID of the loaded spec to set headers for
        headers: Dictionary of HTTP headers to use by default (optional, defaults to empty)

    Returns:
        Confirmation message

    Raises:
        ValueError: If the spec_id doesn't exist

    Example:
        # Load a spec
        load_spec_from_url("https://api.example.com/openapi.json", "my-api")

        # Mount auth headers once
        set_spec_headers("my-api", {"Authorization": "Bearer secret-token"})

        # Make requests without repeating headers
        make_api_request("https://api.example.com/users", spec_id="my-api")
    """
    return _set_spec_headers_impl(spec_id, headers)


def main():
    """Main entry point for the OpenAPI MCP server."""
    logging.basicConfig(level=logging.INFO)
    # Use the module-level mcp instance
    mcp.run()


if __name__ == "__main__":
    main()

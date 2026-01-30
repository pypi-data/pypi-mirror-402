"""OpenAPI Navigator - Specification manager for loading, validating, and indexing specs."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import requests
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class OpenAPISpec:
    """Represents a loaded OpenAPI specification with indexes for fast lookups."""

    def __init__(self, spec_id: str, spec_data: Dict[str, Any]):
        self.spec_id = spec_id
        self.spec_data = spec_data
        self.version = self._detect_version()
        self.default_headers: Dict[str, str] = {}
        self._build_indexes()

    def _detect_version(self) -> str:
        """Detect if this is OpenAPI 3.x or Swagger 2.x."""
        if "openapi" in self.spec_data:
            return "openapi3"
        elif "swagger" in self.spec_data:
            return "swagger2"
        else:
            raise ValueError("Could not determine OpenAPI/Swagger version")

    def _build_indexes(self) -> None:
        """Build fast lookup indexes for endpoints and schemas."""
        self.endpoints = []
        self.schemas = {}

        # Extract endpoints
        if self.version == "openapi3":
            paths = self.spec_data.get("paths", {})
            logger.info(
                f"Building indexes for OpenAPI 3.x spec with {len(paths)} paths"
            )
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method in [
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                        "head",
                        "options",
                        "trace",
                    ]:
                        self.endpoints.append(
                            {
                                "method": method.upper(),
                                "path": path,
                                "summary": operation.get("summary", ""),
                                "operationId": operation.get("operationId", ""),
                                "tags": operation.get("tags", []),
                                "operation": operation,
                            }
                        )
        else:  # swagger2
            paths = self.spec_data.get("paths", {})
            logger.info(
                f"Building indexes for Swagger 2.x spec with {len(paths)} paths"
            )
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method in [
                        "get",
                        "post",
                        "put",
                        "delete",
                        "patch",
                        "head",
                        "options",
                    ]:
                        self.endpoints.append(
                            {
                                "method": method.upper(),
                                "path": path,
                                "summary": operation.get("summary", ""),
                                "operationId": operation.get("operationId", ""),
                                "tags": operation.get("tags", []),
                                "operation": operation,
                            }
                        )

        # Extract schemas
        if self.version == "openapi3":
            schemas = self.spec_data.get("components", {}).get("schemas", {})
        else:  # swagger2
            schemas = self.spec_data.get("definitions", {})

        self.schemas = schemas

        logger.info(
            f"Built indexes: {len(self.endpoints)} endpoints, {len(self.schemas)} schemas"
        )
        if self.endpoints:
            logger.info(f"Sample endpoint: {self.endpoints[0]}")
        if self.schemas:
            logger.info(f"Sample schema names: {list(self.schemas.keys())[:5]}")

    def get_endpoint(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Get a specific endpoint by path and method."""
        for endpoint in self.endpoints:
            if endpoint["path"] == path and endpoint["method"] == method:
                operation = endpoint["operation"]

                # Special handling for root endpoint - provide condensed view to reduce token usage
                if path == "/" and operation:
                    # Check if this is a very large operation (likely contains full API documentation)
                    operation_str = str(operation)
                    if len(operation_str) > 5000:  # If operation is very large
                        return {
                            "summary": operation.get("summary", "API Root Endpoint"),
                            "description": operation.get("description", "")[:500]
                            + (
                                "..."
                                if len(operation.get("description", "")) > 500
                                else ""
                            ),
                            "operationId": operation.get("operationId", ""),
                            "tags": operation.get("tags", []),
                            "_note": "This is a condensed view of the root endpoint. Use summary_only=False on get_endpoint for full details.",
                            "responses": {
                                code: {
                                    "description": resp.get("description", "")[:200]
                                    + (
                                        "..."
                                        if len(resp.get("description", "")) > 200
                                        else ""
                                    ),
                                    "content_types": list(
                                        resp.get("content", {}).keys()
                                    )
                                    if "content" in resp
                                    else [],
                                }
                                for code, resp in list(
                                    operation.get("responses", {}).items()
                                )[:3]  # Limit to first 3 responses
                            },
                        }

                return operation
        return None

    def list_endpoints(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """List endpoints, optionally filtered by tag."""
        logger.info(
            f"list_endpoints called with tag={tag}, self.endpoints has {len(self.endpoints)} items"
        )
        if tag is None:
            result = [
                {
                    "method": e["method"],
                    "path": e["path"],
                    "summary": e["summary"],
                    "operationId": e["operationId"],
                }
                for e in self.endpoints
            ]
            logger.info(f"Returning {len(result)} endpoints (no tag filter)")
            return result

        filtered = []
        for endpoint in self.endpoints:
            if tag in endpoint["tags"]:
                filtered.append(
                    {
                        "method": endpoint["method"],
                        "path": endpoint["path"],
                        "summary": endpoint["summary"],
                        "operationId": endpoint["operationId"],
                    }
                )
        logger.info(f"Returning {len(filtered)} endpoints filtered by tag '{tag}'")
        return filtered

    def search_endpoints(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """Search endpoints using fuzzy matching with pagination.

        Args:
            query: Search query string. Use "" or "a" to get all endpoints.
            limit: Maximum number of results to return (default 50, max 200)
            offset: Number of results to skip for pagination (default 0)

        Returns:
            Dictionary containing:
            - endpoints: List of matching endpoints
            - total: Total number of matches (before pagination)
            - limit: Applied limit
            - offset: Applied offset
            - has_more: Whether there are more results available
        """
        # Validate and clamp limit
        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        # If query is empty or very short, return all endpoints with high scores
        if not query or len(query.strip()) <= 2:
            all_results = []
            for endpoint in self.endpoints:
                all_results.append(
                    {
                        "method": endpoint["method"],
                        "path": endpoint["path"],
                        "summary": endpoint["summary"],
                        "operationId": endpoint["operationId"],
                        "score": 100,
                    }
                )

            # Apply pagination
            total = len(all_results)
            paginated_results = all_results[offset : offset + limit]

            return {
                "endpoints": paginated_results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            }

        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            # Fallback to simple substring search if fuzzywuzzy is not available
            all_results = []
            query_lower = query.lower()
            for endpoint in self.endpoints:
                if (
                    query_lower in endpoint["path"].lower()
                    or query_lower in endpoint["summary"].lower()
                    or query_lower in endpoint["operationId"].lower()
                ):
                    all_results.append(
                        {
                            "method": endpoint["method"],
                            "path": endpoint["path"],
                            "summary": endpoint["summary"],
                            "operationId": endpoint["operationId"],
                            "score": 100,
                        }
                    )

            # Apply pagination
            total = len(all_results)
            paginated_results = all_results[offset : offset + limit]

            return {
                "endpoints": paginated_results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            }

        all_results = []
        for endpoint in self.endpoints:
            # Search in path, summary, operationId
            path_score = fuzz.partial_ratio(query.lower(), endpoint["path"].lower())
            summary_score = fuzz.partial_ratio(
                query.lower(), endpoint["summary"].lower()
            )
            op_id_score = fuzz.partial_ratio(
                query.lower(), endpoint["operationId"].lower()
            )

            # Use the best score
            best_score = max(path_score, summary_score, op_id_score)

            if best_score > 50:  # Threshold for relevance
                all_results.append(
                    {
                        "method": endpoint["method"],
                        "path": endpoint["path"],
                        "summary": endpoint["summary"],
                        "operationId": endpoint["operationId"],
                        "score": best_score,
                    }
                )

        # Sort by relevance score
        all_results.sort(key=lambda x: x["score"], reverse=True)

        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[offset : offset + limit]

        return {
            "endpoints": paginated_results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    def search_schemas(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """Search schema names using fuzzy matching with pagination.

        Args:
            query: Search query string. Use "" or "a" to get all schemas.
            limit: Maximum number of results to return (default 50, max 200)
            offset: Number of results to skip for pagination (default 0)

        Returns:
            Dictionary containing:
            - schemas: List of matching schema names
            - total: Total number of matches (before pagination)
            - limit: Applied limit
            - offset: Applied offset
            - has_more: Whether there are more results available
        """
        # Validate and clamp limit
        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        # If query is empty or very short, return all schemas with high scores
        if not query or len(query.strip()) <= 2:
            all_results = []
            for schema_name in self.schemas.keys():
                all_results.append({"name": schema_name, "score": 100})

            # Apply pagination
            total = len(all_results)
            paginated_results = all_results[offset : offset + limit]

            return {
                "schemas": paginated_results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            }

        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            # Fallback to simple substring search if fuzzywuzzy is not available
            all_results = []
            query_lower = query.lower()
            for schema_name in self.schemas.keys():
                if query_lower in schema_name.lower():
                    all_results.append({"name": schema_name, "score": 100})

            # Apply pagination
            total = len(all_results)
            paginated_results = all_results[offset : offset + limit]

            return {
                "schemas": paginated_results,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            }

        all_results = []
        for schema_name in self.schemas.keys():
            # Search in schema name
            score = fuzz.partial_ratio(query.lower(), schema_name.lower())

            if score > 50:  # Threshold for relevance
                all_results.append({"name": schema_name, "score": score})

        # Sort by relevance score
        all_results.sort(key=lambda x: x["score"], reverse=True)

        # Apply pagination
        total = len(all_results)
        paginated_results = all_results[offset : offset + limit]

        return {
            "schemas": paginated_results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific schema by name."""
        return self.schemas.get(schema_name)

    def get_spec_metadata(self) -> Dict[str, Any]:
        """Get metadata about the OpenAPI specification."""
        metadata = {
            "spec_id": self.spec_id,
            "version": self.version,
            "openapi_version": self.spec_data.get(
                "openapi", self.spec_data.get("swagger", "unknown")
            ),
            "title": self.spec_data.get("info", {}).get("title", ""),
            "description": self.spec_data.get("info", {}).get("description", ""),
            "version_info": self.spec_data.get("info", {}).get("version", ""),
            "contact": self.spec_data.get("info", {}).get("contact", {}),
            "license": self.spec_data.get("info", {}).get("license", {}),
            "terms_of_service": self.spec_data.get("info", {}).get(
                "termsOfService", ""
            ),
            "servers": self.spec_data.get("servers", []),
            "host": self.spec_data.get("host", ""),
            "base_path": self.spec_data.get("basePath", ""),
            "schemes": self.spec_data.get("schemes", []),
            "tags": self.spec_data.get("tags", []),
            "endpoint_count": len(self.endpoints),
            "schema_count": len(self.schemas),
        }
        return metadata

    def list_schemas(self, prefix: Optional[str] = None) -> List[str]:
        """List schema names, optionally filtered by prefix."""
        logger.info(
            f"list_schemas called with prefix={prefix}, self.schemas has {len(self.schemas)} items"
        )
        schema_names = list(self.schemas.keys())
        if prefix:
            schema_names = [
                name for name in schema_names if name.lower().startswith(prefix.lower())
            ]
        logger.info(
            f"Returning {len(schema_names)} schema names (filtered by prefix '{prefix}')"
        )
        return sorted(schema_names)

    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set default headers for API requests using this spec.

        Args:
            headers: Dictionary of HTTP headers to use by default
        """
        self.default_headers = headers.copy() if headers else {}

    def get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests using this spec.

        Returns:
            Copy of the default headers dictionary
        """
        return self.default_headers.copy()


class SpecManager:
    """Manages multiple loaded OpenAPI specifications."""

    def __init__(self):
        self.specs: Dict[str, OpenAPISpec] = {}
        self._openapi3_schema = None
        self._swagger2_schema = None

    def _get_openapi3_schema(self) -> Dict[str, Any]:
        """Get OpenAPI 3.x JSON schema for validation."""
        if self._openapi3_schema is None:
            # Basic OpenAPI 3.x schema - we could load the full one from json-schema.org
            self._openapi3_schema = {
                "type": "object",
                "required": ["openapi", "info", "paths"],
                "properties": {
                    "openapi": {"type": "string"},
                    "info": {"type": "object"},
                    "paths": {"type": "object"},
                },
            }
        return self._openapi3_schema

    def _get_swagger2_schema(self) -> Dict[str, Any]:
        """Get Swagger 2.x JSON schema for validation."""
        if self._swagger2_schema is None:
            # Basic Swagger 2.x schema
            self._swagger2_schema = {
                "type": "object",
                "required": ["swagger", "info", "paths"],
                "properties": {
                    "swagger": {"type": "string"},
                    "info": {"type": "object"},
                    "paths": {"type": "object"},
                },
            }
        return self._swagger2_schema

    def load_spec_from_file(self, file_path: str, spec_id: Optional[str] = None) -> str:
        """Load an OpenAPI spec from a local file."""
        if not Path(file_path).is_absolute():
            raise ValueError("File path must be absolute")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith((".yaml", ".yml")):
                    spec_data = yaml.safe_load(f)
                else:
                    spec_data = json.load(f)

            return self._load_spec(spec_data, spec_id or f"file:{file_path}")

        except Exception as e:
            logger.error(f"Failed to load spec from file {file_path}: {e}")
            raise

    def load_spec_from_url(
        self, url: str, spec_id: Optional[str] = None, verify_ssl: bool = True
    ) -> str:
        """Load an OpenAPI spec from a URL.

        Args:
            url: URL to fetch the OpenAPI spec from
            spec_id: Optional custom identifier for the spec
            verify_ssl: Whether to verify SSL certificates (default: True).
                        Set to False to ignore invalid/self-signed certificates.
        """
        try:
            response = requests.get(url, timeout=30, verify=verify_ssl)
            response.raise_for_status()

            # Robust format detection: try JSON first, fall back to YAML
            try:
                # Try JSON first (most common and fastest to parse)
                spec_data = response.json()
            except (ValueError, TypeError):
                # If JSON fails, try YAML
                try:
                    spec_data = yaml.safe_load(response.text)
                except yaml.YAMLError as e:
                    raise ValueError(f"Failed to parse as JSON or YAML: {e}")

            return self._load_spec(spec_data, spec_id or f"url:{url}")

        except Exception as e:
            logger.error(f"Failed to load spec from URL {url}: {e}")
            raise

    def _load_spec(self, spec_data: Dict[str, Any], spec_id: str) -> str:
        """Internal method to load and validate a spec."""
        try:
            # Basic validation
            if "openapi" in spec_data:
                validate(spec_data, self._get_openapi3_schema())
            elif "swagger" in spec_data:
                validate(spec_data, self._get_swagger2_schema())
            else:
                raise ValueError(
                    "Spec does not appear to be a valid OpenAPI or Swagger document"
                )

            # Create the spec object
            spec = OpenAPISpec(spec_id, spec_data)
            self.specs[spec_id] = spec

            logger.info(
                f"Successfully loaded spec {spec_id} with {len(spec.endpoints)} endpoints and {len(spec.schemas)} schemas"
            )
            return spec_id

        except ValidationError as e:
            logger.warning(f"Spec validation warnings for {spec_id}: {e}")
            # Continue anyway - just warn
            spec = OpenAPISpec(spec_id, spec_data)
            self.specs[spec_id] = spec
            return spec_id
        except Exception as e:
            logger.error(f"Failed to load spec {spec_id}: {e}")
            raise

    def get_spec(self, spec_id: str) -> Optional[OpenAPISpec]:
        """Get a loaded spec by ID."""
        return self.specs.get(spec_id)

    def list_loaded_specs(self) -> List[str]:
        """List IDs of all loaded specs."""
        return list(self.specs.keys())

    def unload_spec(self, spec_id: str) -> bool:
        """Unload a spec by ID."""
        if spec_id in self.specs:
            del self.specs[spec_id]
            logger.info(f"Unloaded spec {spec_id}")
            return True
        return False

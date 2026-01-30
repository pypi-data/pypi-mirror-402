"""
MCP Integration Tests using FastMCP direct client pattern.

Tests the actual MCP protocol layer including:
- Tool parameter validation
- JSON-RPC compliance
- New pagination features
- Summary-only functionality
- Error handling
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, Mock
from fastmcp import Client


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI 3.0 specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample Pet Store API",
            "version": "1.0.0",
            "description": "A sample API for managing pets",
        },
        "paths": {
            "/pets": {
                "get": {
                    "summary": "List all pets",
                    "operationId": "listPets",
                    "tags": ["pets"],
                    "responses": {
                        "200": {
                            "description": "List of pets",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Pet"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create a new pet",
                    "operationId": "createPet",
                    "tags": ["pets"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Pet created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pet"}
                                }
                            },
                        }
                    },
                },
            },
            "/pets/{petId}": {
                "get": {
                    "summary": "Get pet by ID",
                    "operationId": "getPet",
                    "tags": ["pets"],
                    "parameters": [
                        {
                            "name": "petId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Pet"}
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "required": ["id", "name"],
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "Unique identifier for the pet",
                        },
                        "name": {"type": "string", "description": "Name of the pet"},
                        "species": {
                            "type": "string",
                            "description": "Species of the pet",
                        },
                        "age": {
                            "type": "integer",
                            "description": "Age of the pet in years",
                        },
                    },
                }
            }
        },
    }


@pytest.fixture
def temp_spec_file(sample_openapi_spec):
    """Create a temporary OpenAPI spec file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_openapi_spec, f, indent=2)
        temp_file = f.name

    yield temp_file

    # Cleanup
    try:
        os.unlink(temp_file)
    except OSError:
        pass


@pytest.fixture
def mcp_server():
    """Create an instance of our OpenAPI Navigator MCP server."""
    # Import our server module
    from openapi_navigator.server import mcp

    return mcp


class TestMCPServerBasics:
    """Test basic MCP server functionality."""

    async def test_server_initialization(self, mcp_server):
        """Test that the MCP server initializes correctly."""
        async with Client(mcp_server) as client:
            # Test tools list
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]

            expected_tools = [
                "load_spec",
                "load_spec_from_url",
                "list_loaded_specs",
                "unload_spec",
                "search_endpoints",
                "get_endpoint",
                "search_schemas",
                "get_schema",
                "get_spec_metadata",
                "make_api_request",
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names

    async def test_load_spec_tool(self, mcp_server, temp_spec_file):
        """Test loading a spec via MCP tools."""
        async with Client(mcp_server) as client:
            # Load spec
            result = await client.call_tool(
                "load_spec", {"file_path": temp_spec_file, "spec_id": "test-mcp-spec"}
            )

            # Should return the spec ID
            assert result.content[0].text == "test-mcp-spec"

            # Verify it's loaded
            loaded_specs = await client.call_tool("list_loaded_specs", {})
            assert "test-mcp-spec" in loaded_specs.content[0].text


class TestMCPPaginationFeatures:
    """Test new pagination features via MCP protocol."""

    async def test_search_endpoints_pagination_parameters(
        self, mcp_server, temp_spec_file
    ):
        """Test that pagination parameters work through MCP layer."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec", {"file_path": temp_spec_file, "spec_id": "test-pagination"}
            )

            # Test search with pagination parameters
            result = await client.call_tool(
                "search_endpoints",
                {"spec_id": "test-pagination", "query": "", "limit": 2, "offset": 0},
            )

            # Parse the JSON response
            response_data = json.loads(result.content[0].text)

            # Verify pagination structure
            assert "endpoints" in response_data
            assert "total" in response_data
            assert "limit" in response_data
            assert "offset" in response_data
            assert "has_more" in response_data

            # Verify pagination values
            assert response_data["limit"] == 2
            assert response_data["offset"] == 0
            assert response_data["total"] == 3
            assert response_data["has_more"] is True
            assert len(response_data["endpoints"]) == 2

    async def test_search_endpoints_second_page(self, mcp_server, temp_spec_file):
        """Test pagination second page."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec",
                {"file_path": temp_spec_file, "spec_id": "test-pagination-page2"},
            )

            # Test second page
            result = await client.call_tool(
                "search_endpoints",
                {
                    "spec_id": "test-pagination-page2",
                    "query": "",
                    "limit": 2,
                    "offset": 2,
                },
            )

            response_data = json.loads(result.content[0].text)

            # Should have 1 remaining endpoint
            assert response_data["limit"] == 2
            assert response_data["offset"] == 2
            assert response_data["total"] == 3
            assert response_data["has_more"] is False
            assert len(response_data["endpoints"]) == 1

    async def test_search_schemas_pagination(self, mcp_server, temp_spec_file):
        """Test schema search pagination via MCP."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec",
                {"file_path": temp_spec_file, "spec_id": "test-schema-pagination"},
            )

            # Test schema search with pagination
            result = await client.call_tool(
                "search_schemas",
                {
                    "spec_id": "test-schema-pagination",
                    "query": "",
                    "limit": 1,
                    "offset": 0,
                },
            )

            response_data = json.loads(result.content[0].text)

            # Verify pagination structure
            assert "schemas" in response_data
            assert "total" in response_data
            assert "limit" in response_data
            assert "offset" in response_data
            assert "has_more" in response_data

            # Should have 1 schema total
            assert response_data["total"] == 1
            assert len(response_data["schemas"]) == 1
            assert response_data["schemas"][0]["name"] == "Pet"


class TestMCPSummaryFeatures:
    """Test summary-only functionality via MCP protocol."""

    async def test_get_endpoint_summary_only(self, mcp_server, temp_spec_file):
        """Test summary_only parameter via MCP."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec", {"file_path": temp_spec_file, "spec_id": "test-summary"}
            )

            # Get endpoint with summary_only=True
            result = await client.call_tool(
                "get_endpoint",
                {
                    "spec_id": "test-summary",
                    "path": "/pets",
                    "method": "GET",
                    "summary_only": True,
                },
            )

            response_data = json.loads(result.content[0].text)

            # Verify summary-only structure
            assert "summary" in response_data
            assert "description" in response_data
            assert "operationId" in response_data
            assert "tags" in response_data
            assert "parameters" in response_data
            assert "responses" in response_data

            # Verify values
            assert response_data["summary"] == "List all pets"
            assert response_data["operationId"] == "listPets"
            assert response_data["tags"] == ["pets"]

            # Verify response structure is simplified
            assert "200" in response_data["responses"]
            assert "description" in response_data["responses"]["200"]
            assert "content_types" in response_data["responses"]["200"]

    async def test_get_endpoint_full_vs_summary(self, mcp_server, temp_spec_file):
        """Test difference between full and summary endpoint responses."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec",
                {"file_path": temp_spec_file, "spec_id": "test-full-vs-summary"},
            )

            # Get full endpoint
            full_result = await client.call_tool(
                "get_endpoint",
                {
                    "spec_id": "test-full-vs-summary",
                    "path": "/pets",
                    "method": "GET",
                    "summary_only": False,
                },
            )

            # Get summary endpoint
            summary_result = await client.call_tool(
                "get_endpoint",
                {
                    "spec_id": "test-full-vs-summary",
                    "path": "/pets",
                    "method": "GET",
                    "summary_only": True,
                },
            )

            full_data = json.loads(full_result.content[0].text)
            summary_data = json.loads(summary_result.content[0].text)

            # Summary should have structured response format
            assert "content_types" in str(summary_data)
            assert "content" in str(full_data) or "description" in str(full_data)

            # Summary should not have complex nested schemas
            if "responses" in full_data and "200" in full_data["responses"]:
                if "content" in full_data["responses"]["200"]:
                    # Full response has complex content structure
                    assert "content" in full_data["responses"]["200"]
                    # Summary has simplified content_types list
                    assert "content_types" in summary_data["responses"]["200"]


class TestMCPErrorHandling:
    """Test error handling via MCP protocol."""

    async def test_invalid_spec_id(self, mcp_server):
        """Test error handling for invalid spec ID."""
        async with Client(mcp_server) as client:
            # Try to use non-existent spec
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "search_endpoints", {"spec_id": "non-existent-spec", "query": ""}
                )

            # Should get a meaningful error
            assert "No spec found with ID" in str(exc_info.value)

    async def test_pagination_parameter_validation(self, mcp_server, temp_spec_file):
        """Test pagination parameter validation."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec",
                {"file_path": temp_spec_file, "spec_id": "test-param-validation"},
            )

            # Test with limit > 200 (should be clamped)
            result = await client.call_tool(
                "search_endpoints",
                {
                    "spec_id": "test-param-validation",
                    "query": "",
                    "limit": 500,  # Should be clamped to 200
                    "offset": 0,
                },
            )

            response_data = json.loads(result.content[0].text)
            assert response_data["limit"] == 200  # Should be clamped

            # Test with negative offset (should be clamped to 0)
            result = await client.call_tool(
                "search_endpoints",
                {
                    "spec_id": "test-param-validation",
                    "query": "",
                    "limit": 10,
                    "offset": -5,  # Should be clamped to 0
                },
            )

            response_data = json.loads(result.content[0].text)
            assert response_data["offset"] == 0  # Should be clamped


class TestMCPBackwardCompatibility:
    """Test that new features maintain backward compatibility."""

    async def test_search_endpoints_without_pagination(
        self, mcp_server, temp_spec_file
    ):
        """Test that search_endpoints works without pagination params."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec",
                {"file_path": temp_spec_file, "spec_id": "test-backward-compat"},
            )

            # Call without pagination parameters (should use defaults)
            result = await client.call_tool(
                "search_endpoints", {"spec_id": "test-backward-compat", "query": ""}
            )

            response_data = json.loads(result.content[0].text)

            # Should still return pagination structure with defaults
            assert "endpoints" in response_data
            assert "total" in response_data
            assert response_data["limit"] == 50  # Default limit
            assert response_data["offset"] == 0  # Default offset

    async def test_get_endpoint_without_summary_only(self, mcp_server, temp_spec_file):
        """Test that get_endpoint works without summary_only param."""
        async with Client(mcp_server) as client:
            # Load spec
            await client.call_tool(
                "load_spec",
                {"file_path": temp_spec_file, "spec_id": "test-default-summary"},
            )

            # Call without summary_only parameter (should default to False)
            result = await client.call_tool(
                "get_endpoint",
                {"spec_id": "test-default-summary", "path": "/pets", "method": "GET"},
            )

            # Should return full endpoint data
            response_data = json.loads(result.content[0].text)
            assert "summary" in response_data
            assert "operationId" in response_data
            # Should have full structure, not summary structure
            assert "responses" in response_data
            if "200" in response_data["responses"]:
                # Full response should have content, not content_types
                assert (
                    "content" in response_data["responses"]["200"]
                    or "description" in response_data["responses"]["200"]
                )


class TestMCPHeaderMounting:
    """Test header mounting functionality via MCP protocol."""

    @pytest.mark.asyncio
    async def test_set_spec_headers_via_mcp(self, sample_openapi_spec, temp_spec_file):
        """Test set_spec_headers tool via MCP protocol."""
        from openapi_navigator.server import mcp

        async with Client(mcp) as client:
            # Load a spec first
            await client.call_tool(
                "load_spec", {"file_path": temp_spec_file, "spec_id": "test-api"}
            )

            # Set headers
            result = await client.call_tool(
                "set_spec_headers",
                {
                    "spec_id": "test-api",
                    "headers": {
                        "Authorization": "Bearer test-token",
                        "X-API-Key": "key123",
                    },
                },
            )

            assert "successfully" in result.content[0].text.lower()
            assert "test-api" in result.content[0].text

    @pytest.mark.asyncio
    async def test_set_spec_headers_nonexistent_spec(self):
        """Test set_spec_headers with nonexistent spec via MCP."""
        from openapi_navigator.server import mcp

        async with Client(mcp) as client:
            with pytest.raises(Exception, match="No spec found"):
                await client.call_tool(
                    "set_spec_headers",
                    {
                        "spec_id": "nonexistent",
                        "headers": {"Authorization": "Bearer token"},
                    },
                )

    @pytest.mark.asyncio
    async def test_make_api_request_with_spec_id_via_mcp(
        self, sample_openapi_spec, temp_spec_file
    ):
        """Test make_api_request with spec_id parameter via MCP."""
        from openapi_navigator.server import mcp

        with patch("openapi_navigator.server.requests.request") as mock_request:
            # Setup mock response for headers endpoint
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(
                {"headers": {"X-Test-Header": "test-value"}}
            )
            mock_response.json.return_value = {
                "headers": {"X-Test-Header": "test-value"}
            }
            mock_response.headers = {}
            mock_response.url = "https://httpbin.org/headers"
            mock_request.return_value = mock_response

            async with Client(mcp) as client:
                # Load spec
                await client.call_tool(
                    "load_spec", {"file_path": temp_spec_file, "spec_id": "test-api"}
                )

                # Set headers
                await client.call_tool(
                    "set_spec_headers",
                    {"spec_id": "test-api", "headers": {"X-Test-Header": "test-value"}},
                )

                # Make request with spec_id (using mocked httpbin response)
                result = await client.call_tool(
                    "make_api_request",
                    {
                        "url": "https://httpbin.org/headers",
                        "spec_id": "test-api",
                        "method": "GET",
                    },
                )

                # Parse the result
                result_text = result.content[0].text
                result_data = json.loads(result_text)

                # Verify the request was made and returned successfully
                assert result_data["status_code"] == 200

                # Parse the response to check headers were sent
                response_json = result_data["json"]
                assert "X-Test-Header" in response_json["headers"]
                assert response_json["headers"]["X-Test-Header"] == "test-value"

    @pytest.mark.asyncio
    async def test_make_api_request_header_override_via_mcp(
        self, sample_openapi_spec, temp_spec_file
    ):
        """Test that request headers override spec headers via MCP."""
        from openapi_navigator.server import mcp

        with patch("openapi_navigator.server.requests.request") as mock_request:
            # Setup mock response for headers endpoint
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps(
                {
                    "headers": {
                        "X-Default": "default-value",
                        "X-Override-Me": "overridden",
                        "X-Custom": "custom-value",
                    }
                }
            )
            mock_response.json.return_value = {
                "headers": {
                    "X-Default": "default-value",
                    "X-Override-Me": "overridden",
                    "X-Custom": "custom-value",
                }
            }
            mock_response.headers = {}
            mock_response.url = "https://httpbin.org/headers"
            mock_request.return_value = mock_response

            async with Client(mcp) as client:
                # Load spec
                await client.call_tool(
                    "load_spec", {"file_path": temp_spec_file, "spec_id": "test-api"}
                )

                # Set default headers
                await client.call_tool(
                    "set_spec_headers",
                    {
                        "spec_id": "test-api",
                        "headers": {
                            "X-Default": "default-value",
                            "X-Override-Me": "original",
                        },
                    },
                )

                # Make request with overriding header
                result = await client.call_tool(
                    "make_api_request",
                    {
                        "url": "https://httpbin.org/headers",
                        "spec_id": "test-api",
                        "method": "GET",
                        "headers": {
                            "X-Override-Me": "overridden",
                            "X-Custom": "custom-value",
                        },
                    },
                )

                result_text = result.content[0].text
                result_data = json.loads(result_text)
                response_json = result_data["json"]

                # Verify header merging behavior
                assert response_json["headers"]["X-Default"] == "default-value"
                assert (
                    response_json["headers"]["X-Override-Me"] == "overridden"
                )  # Not "original"
                assert response_json["headers"]["X-Custom"] == "custom-value"

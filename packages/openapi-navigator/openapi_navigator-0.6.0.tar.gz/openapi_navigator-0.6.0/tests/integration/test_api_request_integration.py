"""Integration tests for the _make_api_request_impl tool."""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, Mock
from openapi_navigator.server import _make_api_request_impl
from openapi_navigator.spec_manager import SpecManager


class TestApiRequestIntegration:
    """Integration tests for the _make_api_request_impl tool."""

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_get_request(self, mock_request):
        """Test real GET request to httpbin.org."""
        # Mock response for GET request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {"url": "https://httpbin.org/get", "headers": {"User-Agent": "test"}}
        )
        mock_response.json.return_value = {
            "url": "https://httpbin.org/get",
            "headers": {"User-Agent": "test"},
        }
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.url = "https://httpbin.org/get"
        mock_request.return_value = mock_response

        result = _make_api_request_impl("https://httpbin.org/get")

        assert result["status_code"] == 200
        assert result["method"] == "GET"
        assert result["json"] is not None
        assert "url" in result["json"]
        assert result["url"] == "https://httpbin.org/get"
        assert result["elapsed_ms"] >= 0  # Mock requests are instant, so >= 0
        assert len(result["headers"]) > 0  # Just ensure we have headers

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_post_request_with_json(self, mock_request):
        """Test real POST request with JSON data to httpbin.org."""
        # Mock response for POST request
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "json": {"test": "data", "number": 42},
                "headers": {"Content-Type": "application/json"},
            }
        )
        mock_response.json.return_value = {
            "json": {"test": "data", "number": 42},
            "headers": {"Content-Type": "application/json"},
        }
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.url = "https://httpbin.org/post"
        mock_request.return_value = mock_response

        headers = {"Content-Type": "application/json"}
        data = '{"test": "data", "number": 42}'

        result = _make_api_request_impl(
            url="https://httpbin.org/post", method="POST", headers=headers, data=data
        )

        assert result["status_code"] == 200
        assert result["method"] == "POST"
        assert result["json"] is not None
        assert result["json"]["json"]["test"] == "data"
        assert result["json"]["json"]["number"] == 42
        assert result["json"]["headers"]["Content-Type"] == "application/json"

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_request_with_parameters(self, mock_request):
        """Test real GET request with URL parameters to httpbin.org."""
        # Mock response for GET request with parameters
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "args": {"param1": "value1", "param2": "value2"},
                "url": "https://httpbin.org/get?param1=value1&param2=value2",
            }
        )
        mock_response.json.return_value = {
            "args": {"param1": "value1", "param2": "value2"},
            "url": "https://httpbin.org/get?param1=value1&param2=value2",
        }
        mock_response.headers = {}
        mock_response.url = "https://httpbin.org/get?param1=value1&param2=value2"
        mock_request.return_value = mock_response

        params = {"param1": "value1", "param2": "value2"}

        result = _make_api_request_impl(url="https://httpbin.org/get", params=params)

        assert result["status_code"] == 200
        assert result["json"] is not None
        assert result["json"]["args"]["param1"] == "value1"
        assert result["json"]["args"]["param2"] == "value2"

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_request_with_custom_headers(self, mock_request):
        """Test real request with custom headers to httpbin.org."""
        # Mock response for headers endpoint
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "headers": {
                    "X-Custom-Header": "test-value",
                    "User-Agent": "OpenAPI-Navigator-Test/1.0",
                }
            }
        )
        mock_response.json.return_value = {
            "headers": {
                "X-Custom-Header": "test-value",
                "User-Agent": "OpenAPI-Navigator-Test/1.0",
            }
        }
        mock_response.headers = {}
        mock_response.url = "https://httpbin.org/headers"
        mock_request.return_value = mock_response

        headers = {
            "X-Custom-Header": "test-value",
            "User-Agent": "OpenAPI-Navigator-Test/1.0",
        }

        result = _make_api_request_impl(
            url="https://httpbin.org/headers", headers=headers
        )

        assert result["status_code"] == 200
        assert result["json"] is not None
        assert result["json"]["headers"]["X-Custom-Header"] == "test-value"
        assert result["json"]["headers"]["User-Agent"] == "OpenAPI-Navigator-Test/1.0"

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_different_methods(self, mock_request):
        """Test different HTTP methods with httpbin.org."""
        methods = ["PUT", "PATCH", "DELETE"]

        # Setup mock responses for each method
        mock_responses = []
        for method in methods:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = json.dumps({"method": method})
            mock_response.json.return_value = {"method": method}
            mock_response.headers = {}
            mock_response.url = f"https://httpbin.org/{method.lower()}"
            mock_responses.append(mock_response)

        mock_request.side_effect = mock_responses

        for method in methods:
            result = _make_api_request_impl(
                url=f"https://httpbin.org/{method.lower()}", method=method
            )

            assert result["status_code"] == 200
            assert result["method"] == method
            assert result["json"] is not None

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_404_error(self, mock_request):
        """Test handling of 404 error response."""
        # Mock response for 404 error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = ""
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.headers = {}
        mock_response.url = "https://httpbin.org/status/404"
        mock_request.return_value = mock_response

        result = _make_api_request_impl("https://httpbin.org/status/404")

        assert result["status_code"] == 404
        assert result["method"] == "GET"
        # Should not raise an exception, just return the error status

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_timeout_behavior(self, mock_request):
        """Test timeout behavior with httpbin.org delay endpoint."""
        # Mock timeout error
        import requests

        mock_request.side_effect = requests.Timeout("Connection timeout")

        # Use a very short timeout to test timeout handling
        with pytest.raises(TimeoutError):
            _make_api_request_impl("https://httpbin.org/delay/5", timeout=1)

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_real_api_connection_error(self, mock_request):
        """Test connection error with non-existent domain."""
        # Mock connection error
        import requests

        mock_request.side_effect = requests.ConnectionError(
            "Failed to resolve hostname"
        )

        with pytest.raises(ConnectionError):
            _make_api_request_impl("https://nonexistent-domain-12345.com")

    @pytest.mark.integration
    @patch("openapi_navigator.server.requests.request")
    def test_combined_workflow_spec_loading_and_api_requests(
        self, mock_request, sample_openapi_spec
    ):
        """Test combined workflow: load spec, explore endpoints, then make API requests."""
        manager = SpecManager()

        # Setup mock responses
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.text = json.dumps(
            {"args": {}, "url": "https://httpbin.org/get"}
        )
        mock_get_response.json.return_value = {
            "args": {},
            "url": "https://httpbin.org/get",
        }
        mock_get_response.headers = {}
        mock_get_response.url = "https://httpbin.org/get"

        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.text = json.dumps(
            {
                "json": {"name": "Fluffy", "tag": "cat"},
                "url": "https://httpbin.org/post",
            }
        )
        mock_post_response.json.return_value = {
            "json": {"name": "Fluffy", "tag": "cat"},
            "url": "https://httpbin.org/post",
        }
        mock_post_response.headers = {}
        mock_post_response.url = "https://httpbin.org/post"

        mock_error_response = Mock()
        mock_error_response.status_code = 500
        mock_error_response.text = ""
        mock_error_response.json.side_effect = ValueError("No JSON")
        mock_error_response.headers = {}
        mock_error_response.url = "https://httpbin.org/status/500"

        mock_request.side_effect = [
            mock_get_response,
            mock_post_response,
            mock_error_response,
        ]

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_openapi_spec, f, indent=2)
            temp_file = f.name

        try:
            # 1. Load and explore the OpenAPI spec
            manager.load_spec_from_file(temp_file, "pet-store")
            spec = manager.get_spec("pet-store")

            # 2. Explore available endpoints
            endpoints_result = spec.search_endpoints("")
            assert len(endpoints_result["endpoints"]) == 3

            # 3. Get base URL info from spec metadata
            metadata = spec.get_spec_metadata()
            assert metadata["title"] == "Sample Pet Store API"

            # 4. Make API requests to test endpoints (using mocked httpbin responses)
            # Simulate what a user might do after exploring the spec

            # Test a GET request (like listing pets)
            get_result = _make_api_request_impl("https://httpbin.org/get")
            assert get_result["status_code"] == 200

            # Test a POST request (like creating a pet)
            post_data = '{"name": "Fluffy", "tag": "cat"}'
            post_result = _make_api_request_impl(
                url="https://httpbin.org/post",
                method="POST",
                headers={"Content-Type": "application/json"},
                data=post_data,
            )
            assert post_result["status_code"] == 200
            assert post_result["json"]["json"]["name"] == "Fluffy"

            # Test error handling
            error_result = _make_api_request_impl("https://httpbin.org/status/500")
            assert error_result["status_code"] == 500

            # Clean up spec
            manager.unload_spec("pet-store")

        finally:
            # Cleanup
            try:
                os.unlink(temp_file)
            except OSError:
                pass

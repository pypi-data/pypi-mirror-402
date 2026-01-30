"""
End-to-end integration test for header mounting workflow.

This test simulates a real agent workflow:
1. Load an API spec
2. Mount auth headers
3. Make multiple requests without repeating headers
4. Override headers when needed

Tests use mocked HTTP requests to avoid external dependencies.
"""

import json
import tempfile
import os
from unittest.mock import patch, Mock
from openapi_navigator.server import _make_api_request_impl, _spec_manager


class TestHeaderMountingWorkflow:
    """Test complete header mounting workflow."""

    def setup_method(self):
        """Clear specs before each test."""
        _spec_manager.specs.clear()
        self.manager = _spec_manager

    @patch("openapi_navigator.server.requests.request")
    def test_complete_workflow_with_mocked_api(self, mock_request, sample_openapi_spec):
        """Test the complete header mounting workflow with mocked HTTP calls."""

        # Setup mock response for /headers endpoint
        mock_headers_response = Mock()
        mock_headers_response.status_code = 200
        mock_headers_response.text = json.dumps(
            {
                "headers": {
                    "Authorization": "Bearer test-token-123",
                    "X-Api-Key": "key-456",
                    "X-Custom-Test": "workflow-test",
                }
            }
        )
        mock_headers_response.json.return_value = {
            "headers": {
                "Authorization": "Bearer test-token-123",
                "X-Api-Key": "key-456",
                "X-Custom-Test": "workflow-test",
            }
        }
        mock_headers_response.headers = {}
        mock_headers_response.url = "https://httpbin.org/headers"

        # Setup mock response for /get endpoint
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.text = json.dumps(
            {"args": {}, "headers": {}, "url": "https://httpbin.org/get"}
        )
        mock_get_response.json.return_value = {
            "args": {},
            "headers": {},
            "url": "https://httpbin.org/get",
        }
        mock_get_response.headers = {}
        mock_get_response.url = "https://httpbin.org/get"

        mock_request.side_effect = [
            mock_headers_response,
            mock_headers_response,
            mock_get_response,
        ]

        # Step 1: Load a spec from temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_openapi_spec, f)
            temp_file = f.name

        try:
            spec_id = self.manager.load_spec_from_file(temp_file, "petstore")
            assert spec_id == "petstore"
        finally:
            os.unlink(temp_file)

        # Step 2: Mount headers
        spec = self.manager.get_spec("petstore")
        spec.set_headers(
            {
                "Authorization": "Bearer test-token-123",
                "X-API-Key": "key-456",
                "X-Custom-Test": "workflow-test",
            }
        )
        mounted_headers = spec.get_headers()
        assert len(mounted_headers) == 3
        assert mounted_headers["Authorization"] == "Bearer test-token-123"

        # Step 3: Verify the headers are actually in the spec
        spec = self.manager.get_spec("petstore")
        spec_headers = spec.get_headers()
        assert "Authorization" in spec_headers
        assert spec_headers["Authorization"] == "Bearer test-token-123"
        assert spec_headers["X-API-Key"] == "key-456"
        assert spec_headers["X-Custom-Test"] == "workflow-test"

        # Step 4: Make request using mounted headers and verify headers were passed
        response = _make_api_request_impl(
            url="https://httpbin.org/headers", spec_id="petstore", method="GET"
        )

        # Verify the request was successful
        assert response["status_code"] == 200
        assert response["json"] is not None

        # Verify the mock was called with the correct headers
        first_call = mock_request.call_args_list[0]
        assert first_call.kwargs["headers"]["Authorization"] == "Bearer test-token-123"
        assert first_call.kwargs["headers"]["X-API-Key"] == "key-456"
        assert first_call.kwargs["headers"]["X-Custom-Test"] == "workflow-test"

        # Step 5: Make another request, verify headers still applied
        response2 = _make_api_request_impl(
            url="https://httpbin.org/headers", spec_id="petstore"
        )

        # Verify the request completed with expected structure
        assert response2["status_code"] == 200
        assert "headers" in response2

        # Verify the second request also had the mounted headers
        second_call = mock_request.call_args_list[1]
        assert second_call.kwargs["headers"]["Authorization"] == "Bearer test-token-123"

        # Step 6: Test override - verify headers parameter overrides spec headers
        response3 = _make_api_request_impl(
            url="https://httpbin.org/get",
            spec_id="petstore",
            headers={"Authorization": "Bearer override-token", "X-Custom": "override"},
        )

        # Verify the request completed
        assert response3["status_code"] == 200

        # Verify the override headers were used (not the spec headers)
        third_call = mock_request.call_args_list[2]
        assert third_call.kwargs["headers"]["Authorization"] == "Bearer override-token"
        assert third_call.kwargs["headers"]["X-Custom"] == "override"
        # The X-API-Key from spec should still be there
        assert third_call.kwargs["headers"]["X-API-Key"] == "key-456"

        # Step 7: Clear headers
        spec.set_headers({})
        assert spec.get_headers() == {}

        # Step 8: Unload spec
        success = self.manager.unload_spec("petstore")
        assert success

    @patch("openapi_navigator.server.requests.request")
    def test_multiple_specs_with_different_headers(
        self, mock_request, sample_openapi_spec
    ):
        """Test managing headers for multiple specs simultaneously with mocked HTTP."""

        # Setup mock responses
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.text = json.dumps({"data": "api-1-response"})
        mock_response1.json.return_value = {"data": "api-1-response"}
        mock_response1.headers = {}
        mock_response1.url = "https://httpbin.org/json"

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.text = json.dumps({"data": "api-2-response"})
        mock_response2.json.return_value = {"data": "api-2-response"}
        mock_response2.headers = {}
        mock_response2.url = "https://httpbin.org/json"

        mock_request.side_effect = [mock_response1, mock_response2]

        # Load two specs with different headers
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_openapi_spec, f)
            temp_file = f.name

        try:
            self.manager.load_spec_from_file(temp_file, "api-1")
            self.manager.load_spec_from_file(temp_file, "api-2")
        finally:
            os.unlink(temp_file)

        # Set different headers for each
        spec1 = self.manager.get_spec("api-1")
        spec2 = self.manager.get_spec("api-2")
        spec1.set_headers({"Authorization": "Bearer token-1", "X-Test-1": "value1"})
        spec2.set_headers({"Authorization": "Bearer token-2", "X-Test-2": "value2"})

        # Verify each spec maintains independent headers
        assert spec1.get_headers() == {
            "Authorization": "Bearer token-1",
            "X-Test-1": "value1",
        }
        assert spec2.get_headers() == {
            "Authorization": "Bearer token-2",
            "X-Test-2": "value2",
        }

        # Make request to api-1 and verify its headers were sent
        response1 = _make_api_request_impl("https://httpbin.org/json", spec_id="api-1")
        assert response1["status_code"] == 200
        assert response1["json"] is not None

        # Verify api-1's headers were passed in the request
        first_call = mock_request.call_args_list[0]
        assert first_call.kwargs["headers"]["Authorization"] == "Bearer token-1"
        assert first_call.kwargs["headers"]["X-Test-1"] == "value1"

        # Make request to api-2 and verify its headers were sent
        response2 = _make_api_request_impl("https://httpbin.org/json", spec_id="api-2")
        assert response2["status_code"] == 200
        assert response2["json"] is not None

        # Verify api-2's headers were passed in the request
        second_call = mock_request.call_args_list[1]
        assert second_call.kwargs["headers"]["Authorization"] == "Bearer token-2"
        assert second_call.kwargs["headers"]["X-Test-2"] == "value2"

        # Verify we can still access both specs' headers
        assert spec1.get_headers()["Authorization"] == "Bearer token-1"
        assert spec2.get_headers()["Authorization"] == "Bearer token-2"

        # Cleanup
        self.manager.unload_spec("api-1")
        self.manager.unload_spec("api-2")

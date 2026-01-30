#!/usr/bin/env python3
"""Test the uncommitted local changes directly."""

import sys
import os
import json

# Add the src directory to the path to import local modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from openapi_navigator.spec_manager import SpecManager

def test_local_changes():
    """Test the uncommitted changes in our local code."""
    print("Testing Local OpenAPI Navigator Changes")
    print("=" * 50)

    # Create spec manager
    manager = SpecManager()

    # Load our test spec
    spec_id = manager.load_spec_from_file("/Users/michaelgaruccio/code/openapi-mcp/test_spec.json", "test-local")
    print(f"✓ Loaded spec: {spec_id}")

    # Get the spec object
    spec = manager.get_spec(spec_id)

    # Test new pagination functionality in search_endpoints
    print("\n=== Testing search_endpoints Pagination ===")

    # Test with no pagination (should return new format)
    result = spec.search_endpoints("")
    print(f"All endpoints: {json.dumps(result, indent=2)}")

    # Test with pagination parameters
    result_paginated = spec.search_endpoints("", limit=2, offset=0)
    print(f"Paginated (limit=2, offset=0): {json.dumps(result_paginated, indent=2)}")

    # Test second page
    result_page2 = spec.search_endpoints("", limit=2, offset=2)
    print(f"Paginated (limit=2, offset=2): {json.dumps(result_page2, indent=2)}")

    # Test new pagination functionality in search_schemas
    print("\n=== Testing search_schemas Pagination ===")

    schemas_result = spec.search_schemas("")
    print(f"All schemas: {json.dumps(schemas_result, indent=2)}")

    schemas_paginated = spec.search_schemas("", limit=1, offset=0)
    print(f"Paginated schemas: {json.dumps(schemas_paginated, indent=2)}")

    # Test new summary_only functionality in get_endpoint
    print("\n=== Testing get_endpoint summary_only ===")

    # Get full endpoint
    full_endpoint = spec.get_endpoint("/pets", "GET")
    print(f"Full endpoint keys: {list(full_endpoint.keys()) if full_endpoint else 'None'}")

    # Test the new summary_only parameter in the spec_manager code
    # Since the MCP tool wrapper has the functionality, let's test it directly
    endpoint = spec.get_endpoint("/pets", "GET")
    if endpoint:
        # Simulate what the server.py summary_only logic does
        summary_endpoint = {
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
                    "content_types": list(resp.get("content", {}).keys())
                    if "content" in resp
                    else [],
                }
                for code, resp in endpoint.get("responses", {}).items()
            },
        }
        print(f"Summary endpoint: {json.dumps(summary_endpoint, indent=2)}")

    print("\n✓ All local functionality tests completed!")

if __name__ == "__main__":
    test_local_changes()
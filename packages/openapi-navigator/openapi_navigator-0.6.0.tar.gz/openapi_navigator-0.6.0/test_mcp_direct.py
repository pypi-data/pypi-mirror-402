#!/usr/bin/env python3
"""
Test script to interact with the OpenAPI Navigator MCP server directly.
"""
import json
import subprocess
import sys
import os

def send_mcp_request(server_cmd, request):
    """Send a JSON-RPC request to the MCP server and get response."""
    try:
        proc = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )

        # Send request
        request_str = json.dumps(request) + '\n'
        stdout, stderr = proc.communicate(input=request_str, timeout=30)

        if stderr:
            print(f"STDERR: {stderr}", file=sys.stderr)

        # Parse response
        if stdout.strip():
            return json.loads(stdout.strip())
        else:
            return None

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def test_openapi_navigator():
    """Test the OpenAPI Navigator MCP server."""
    server_cmd = ["uv", "run", "openapi-navigator"]

    # Test 1: Initialize
    print("=== Testing MCP Server Initialization ===")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    response = send_mcp_request(server_cmd, init_request)
    if response:
        print(f"Init Response: {json.dumps(response, indent=2)}")
    else:
        print("Failed to get init response")
        return False

    # Test 2: List tools
    print("\n=== Testing Tool Listing ===")
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    response = send_mcp_request(server_cmd, list_tools_request)
    if response:
        print(f"Tools: {json.dumps(response, indent=2)}")
        tools = response.get('result', {}).get('tools', [])
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.get('name')}: {tool.get('description', '')[:60]}...")
    else:
        print("Failed to get tools list")
        return False

    return True

def test_tool_calls():
    """Test specific tool calls with our new functionality."""
    server_cmd = ["uv", "run", "openapi-navigator"]

    # First initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }

    proc = subprocess.Popen(
        server_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Initialize
        request_str = json.dumps(init_request) + '\n'
        proc.stdin.write(request_str)
        proc.stdin.flush()

        # Read initialization response
        init_response = proc.stdout.readline()
        print(f"Init: {init_response.strip()}")

        # Test load_spec tool call
        print("\n=== Testing load_spec Tool ===")
        load_spec_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "load_spec",
                "arguments": {
                    "file_path": "/Users/michaelgaruccio/code/openapi-mcp/tests/fixtures/petstore_openapi3.json"
                }
            }
        }

        request_str = json.dumps(load_spec_request) + '\n'
        proc.stdin.write(request_str)
        proc.stdin.flush()

        response = proc.stdout.readline()
        print(f"Load Spec: {response.strip()}")

        # Test search_endpoints with pagination
        print("\n=== Testing search_endpoints with Pagination ===")
        search_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_endpoints",
                "arguments": {
                    "spec_id": "file:/Users/michaelgaruccio/code/openapi-mcp/tests/fixtures/petstore_openapi3.json",
                    "query": "",
                    "limit": 2,
                    "offset": 0
                }
            }
        }

        request_str = json.dumps(search_request) + '\n'
        proc.stdin.write(request_str)
        proc.stdin.flush()

        response = proc.stdout.readline()
        print(f"Search Endpoints: {response.strip()}")

        # Test get_endpoint with summary_only
        print("\n=== Testing get_endpoint with summary_only ===")
        get_endpoint_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_endpoint",
                "arguments": {
                    "spec_id": "file:/Users/michaelgaruccio/code/openapi-mcp/tests/fixtures/petstore_openapi3.json",
                    "path": "/pets",
                    "method": "GET",
                    "summary_only": True
                }
            }
        }

        request_str = json.dumps(get_endpoint_request) + '\n'
        proc.stdin.write(request_str)
        proc.stdin.flush()

        response = proc.stdout.readline()
        print(f"Get Endpoint (summary): {response.strip()}")

    except Exception as e:
        print(f"Error during tool testing: {e}")
    finally:
        proc.terminate()

if __name__ == "__main__":
    print("Testing OpenAPI Navigator MCP Server")
    print("=" * 50)

    # Run basic tests
    if test_openapi_navigator():
        print("\n" + "=" * 50)
        print("Basic tests passed! Now testing tool calls...")
        test_tool_calls()
    else:
        print("Basic tests failed!")
        sys.exit(1)
# MCP Inspector Testing Guide

This guide covers how to use MCP Inspector and other CLI tools to test the OpenAPI Navigator MCP server.

## Testing Tools Overview

### 1. Official MCP Inspector
The official testing tool from the Model Context Protocol team with both web UI and CLI modes.

**Features:**
- Interactive web interface at http://localhost:6274
- CLI mode for automation and scripting
- Support for stdio, SSE, and HTTP transports
- Tool testing, resource access, and prompt interaction

### 2. MCP CLI (wong2/mcp-cli)
Alternative CLI tool with OAuth support and JSON configuration.

### 3. MCP Tools (f/mcptools)
Go-based CLI with Homebrew installation and unified interface.

## Installation Options

### Option 1: Official MCP Inspector (Recommended)
```bash
# No installation needed - use npx
npx @modelcontextprotocol/inspector --version
```

### Option 2: Alternative CLI Tools
```bash
# MCP CLI
npm install -g @wong2/mcp-cli

# MCP Tools (Homebrew)
brew tap f/mcptools && brew install mcp
```

## Testing Our OpenAPI Navigator Server

### Web UI Testing

1. **Start the MCP Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector uv run openapi-navigator
   ```

2. **Access the interface**: Open http://localhost:6274 in your browser

3. **Test workflow**:
   - View available tools in the Tools section
   - Load an OpenAPI spec using `load_spec` or `load_spec_from_url`
   - Search endpoints with `search_endpoints`
   - Get endpoint details with `get_endpoint`
   - Test pagination parameters
   - Make API requests with `make_api_request`

### CLI Testing

#### Basic Tool Listing
```bash
# List all available tools
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator
```

#### Tool Testing Examples

**Important Limitation**: Each CLI call creates a new server instance, so loaded specs don't persist between calls. Use single operations or the web UI for workflows.

```bash
# List available tools
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/list

# Load a spec (single operation)
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/call \
  --tool-name load_spec_from_url \
  --tool-arg spec_id=petstore \
  --tool-arg url=https://petstore3.swagger.io/api/v3/openapi.json

# Make API request (stateless operation)
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/call \
  --tool-name make_api_request \
  --tool-arg url=https://httpbin.org/get \
  --tool-arg method=GET

# Note: Cannot chain operations like load_spec then search_endpoints in CLI mode
# Use web UI or FastMCP tests for workflows requiring state persistence
```

### Configuration File Testing

Create a configuration file for repeated testing:

```json
{
  "servers": {
    "openapi_navigator": {
      "command": "uv",
      "args": ["run", "openapi-navigator"],
      "env": {
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

Use with:
```bash
npx @modelcontextprotocol/inspector --config inspector-config.json --server openapi_navigator
```

## Automated Testing Script

Create a test script for CI/CD:

```bash
#!/bin/bash
# test-mcp-inspector.sh

set -e

echo "Testing OpenAPI Navigator with MCP Inspector..."

# Test 1: List tools
echo "1. Listing available tools..."
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator list-tools

# Test 2: Load spec
echo "2. Loading OpenAPI spec..."
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator \
  call-tool load_spec_from_url \
  --args '{"url": "https://petstore3.swagger.io/api/v3/openapi.json", "spec_id": "test"}'

# Test 3: Search endpoints
echo "3. Searching endpoints..."
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator \
  call-tool search_endpoints \
  --args '{"spec_id": "test", "query": "", "limit": 3}'

# Test 4: Get endpoint
echo "4. Getting endpoint details..."
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator \
  call-tool get_endpoint \
  --args '{"spec_id": "test", "path": "/pet", "method": "POST"}'

echo "All tests completed successfully!"
```

## Integration with Makefile

Add these targets to your Makefile:

```makefile
inspect:  ## Start MCP Inspector web UI
	npx @modelcontextprotocol/inspector uv run openapi-navigator

inspect-cli:  ## Run MCP Inspector in CLI mode
	npx @modelcontextprotocol/inspector --cli uv run openapi-navigator

test-inspector:  ## Run automated MCP Inspector tests
	./scripts/test-mcp-inspector.sh
```

## Debugging and Troubleshooting

### Common Issues

1. **Server startup fails**: Check that `uv run openapi-navigator` works independently
2. **Tool calls fail**: Verify JSON argument formatting
3. **Web UI doesn't load**: Ensure port 6274 is available
4. **CLI hangs**: Check for proper server termination

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=debug npx @modelcontextprotocol/inspector uv run openapi-navigator
```

### Verbose Output
```bash
# CLI with verbose output
npx @modelcontextprotocol/inspector --cli --verbose uv run openapi-navigator
```

## Best Practices

1. **Test incrementally**: Start with tool listing, then basic operations
2. **Use realistic data**: Test with actual OpenAPI specs from your domain
3. **Validate responses**: Check that tool outputs match expected schemas
4. **Error testing**: Test invalid inputs and error conditions
5. **Performance testing**: Test with large OpenAPI specs to verify pagination
6. **Automation**: Include MCP Inspector tests in CI/CD pipelines

## Comparison with Other Testing Methods

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| MCP Inspector Web UI | Interactive testing, demos | Visual, easy to use | Manual process |
| MCP Inspector CLI | Automation, CI/CD | Scriptable, repeatable | Command-line only |
| FastMCP Tests | Unit/integration testing | Fast, isolated | Requires test code |
| Nanobot Demo | Stakeholder demos | Realistic usage | Setup complexity |

Use MCP Inspector for development and debugging, FastMCP for automated testing, and nanobot for demonstrations.
# Setting Up MCP Inspector in Your Repository

This guide shows how to integrate MCP Inspector testing into any MCP server repository.

## Prerequisites

- Node.js and npm (for npx)
- Working MCP server
- Optional: Make or other build system

## Quick Setup

### 1. Add Inspector Commands to Makefile

Add these targets to your `Makefile`:

```makefile
.PHONY: inspect inspect-cli test-inspector

inspect:  ## Start MCP Inspector web UI
	@echo "Starting MCP Inspector web UI..."
	@echo "Inspector will be available at http://localhost:6274"
	npx @modelcontextprotocol/inspector your-server-command

inspect-cli:  ## Run MCP Inspector in CLI mode (list tools)
	@echo "Running MCP Inspector CLI to list tools..."
	npx @modelcontextprotocol/inspector --cli your-server-command --method tools/list

test-inspector:  ## Run automated MCP Inspector tests
	@echo "Testing MCP server with Inspector..."
	@echo "1. Listing available tools..."
	npx @modelcontextprotocol/inspector --cli your-server-command --method tools/list | head -20
	@echo ""
	@echo "2. Testing stateless operations..."
	npx @modelcontextprotocol/inspector --cli your-server-command --method tools/call \
		--tool-name your-tool-name \
		--tool-arg param1=value1 \
		--tool-arg param2=value2
	@echo "Inspector tests completed!"
```

### 2. Replace Server Command

Replace `your-server-command` with your actual server startup command:

**Examples:**
- Node.js: `node build/index.js`
- Python with uv: `uv run your-package`
- Python with pip: `python -m your_package`
- Binary: `/path/to/your-server`

### 3. Common Server Command Patterns

```makefile
# Node.js built server
inspect:
	npx @modelcontextprotocol/inspector node build/index.js

# Python package with uv
inspect:
	npx @modelcontextprotocol/inspector uv run your-package

# Python script
inspect:
	npx @modelcontextprotocol/inspector python src/server.py

# Rust binary
inspect:
	npx @modelcontextprotocol/inspector ./target/release/your-server

# Go binary
inspect:
	npx @modelcontextprotocol/inspector ./bin/your-server
```

## Advanced Configuration

### Environment Variables

Pass environment variables to your server:

```makefile
inspect:
	npx @modelcontextprotocol/inspector -e LOG_LEVEL=debug -e API_KEY=test uv run your-server

# Or separate inspector flags from server args
inspect:
	npx @modelcontextprotocol/inspector -e LOG_LEVEL=debug -- uv run your-server --verbose
```

### Custom Ports

Override default ports (6274 for UI, 6277 for proxy):

```makefile
inspect:
	CLIENT_PORT=8080 SERVER_PORT=9000 npx @modelcontextprotocol/inspector uv run your-server
```

### Configuration Files

Create `inspector-config.json` for complex setups:

```json
{
  "mcpServers": {
    "dev": {
      "command": "uv",
      "args": ["run", "your-server"],
      "env": {
        "LOG_LEVEL": "debug",
        "ENV": "development"
      }
    },
    "prod": {
      "command": "your-binary",
      "args": ["--config", "prod.json"],
      "env": {
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

Use with:
```makefile
inspect-config:
	npx @modelcontextprotocol/inspector --config inspector-config.json --server dev
```

## Testing Integration

### 1. Add to CI/CD

GitHub Actions example:

```yaml
# .github/workflows/test.yml
name: Test MCP Server
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      # Your server setup steps here

      - name: Test MCP functionality
        run: make test-inspector
```

### 2. Package.json Scripts

For Node.js projects, add to `package.json`:

```json
{
  "scripts": {
    "inspect": "npx @modelcontextprotocol/inspector node build/index.js",
    "inspect:cli": "npx @modelcontextprotocol/inspector --cli node build/index.js --method tools/list",
    "test:mcp": "npm run inspect:cli"
  }
}
```

### 3. Documentation

Add to your README.md:

```markdown
## Testing with MCP Inspector

### Web UI (Interactive)
```bash
make inspect
# Open http://localhost:6274
```

### CLI (Automation)
```bash
make inspect-cli        # List tools
make test-inspector     # Run test suite
```
```

## Project Structure

Recommended file organization:

```
your-repo/
├── Makefile              # Inspector targets
├── inspector-config.json # Optional config
├── docs/
│   └── inspector.md      # This guide
├── tests/
│   └── test_inspector.sh # Custom test scripts
└── src/
    └── your-server.*     # Your MCP server
```

## Tool-Specific Testing

### Customize Test Commands

Replace the generic test with your actual tools:

```makefile
test-inspector:
	@echo "Testing file operations..."
	npx @modelcontextprotocol/inspector --cli your-server --method tools/call \
		--tool-name read_file \
		--tool-arg path=README.md

	@echo "Testing search functionality..."
	npx @modelcontextprotocol/inspector --cli your-server --method tools/call \
		--tool-name search \
		--tool-arg query=test \
		--tool-arg limit=5
```

### Stateful vs Stateless Tools

**Stateless tools** (work well with CLI):
- File operations
- API requests
- Calculations
- Validations

**Stateful tools** (use web UI):
- Database operations
- Session management
- Multi-step workflows
- Resource loading

## Best Practices

### 1. Start Simple
```makefile
# Minimal setup - just list tools
inspect-cli:
	npx @modelcontextprotocol/inspector --cli your-server --method tools/list
```

### 2. Add Error Handling
```makefile
test-inspector:
	@echo "Testing server startup..."
	@npx @modelcontextprotocol/inspector --cli your-server --method tools/list > /dev/null || \
		(echo "❌ Server failed to start" && exit 1)
	@echo "✅ Server started successfully"
```

### 3. Document Limitations
- CLI mode doesn't persist state between calls
- Each CLI invocation starts a new server instance
- Use web UI for complex workflows
- Use FastMCP or custom tests for stateful testing

### 4. Version in Comments
```makefile
# MCP Inspector targets
# Requires @modelcontextprotocol/inspector@^0.16.0
inspect:
	npx @modelcontextprotocol/inspector@latest your-server
```

## Troubleshooting

### Common Issues

1. **Server won't start**
   ```bash
   # Test server independently first
   your-server-command
   ```

2. **Port conflicts**
   ```bash
   # Use different ports
   CLIENT_PORT=8080 make inspect
   ```

3. **Tool calls fail**
   ```bash
   # Verify tool name and arguments
   make inspect-cli
   ```

4. **State doesn't persist**
   - Expected behavior in CLI mode
   - Use web UI for workflows

### Debug Mode
```makefile
inspect-debug:
	LOG_LEVEL=debug npx @modelcontextprotocol/inspector your-server
```

## Integration Examples

### OpenAPI Navigator (Reference)
```makefile
inspect:  ## Start MCP Inspector web UI
	npx @modelcontextprotocol/inspector uv run openapi-navigator

test-inspector:  ## Test with real API
	npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/call \
		--tool-name load_spec_from_url \
		--tool-arg spec_id=test \
		--tool-arg url=https://petstore3.swagger.io/api/v3/openapi.json
```

### File System Server
```makefile
inspect:
	npx @modelcontextprotocol/inspector npx @modelcontextprotocol/server-filesystem /path/to/directory

test-inspector:
	npx @modelcontextprotocol/inspector --cli npx @modelcontextprotocol/server-filesystem /tmp --method tools/call \
		--tool-name read_file \
		--tool-arg path=/tmp/test.txt
```

This setup provides comprehensive MCP testing capabilities for any repository with minimal configuration.
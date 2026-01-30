# Using Nanobot to Demo MCP Server Functionality

This guide explains how to use [nanobot.ai](https://nanobot.ai) to create interactive demos of Model Context Protocol (MCP) servers.

## Prerequisites

1. **Install nanobot**:
   ```bash
   brew install nanobot-ai/tap/nanobot
   ```

2. **Set up API keys** in `.env` file:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   # OR
   OPENAI_API_KEY=sk-your-openai-key
   ```

## Configuration Structure

Create a `nanobot.yaml` configuration file with three main sections:

### 1. Agents Configuration
Define AI agents that will use your MCP server:

```yaml
agents:
  your_agent_name:
    name: "Display Name for Agent"
    model: "claude-sonnet-4-20250514"  # or gpt-4, etc.
    description: |
      Multi-line description of what this agent can do.
      - Feature 1
      - Feature 2
    mcpServers: [your_mcp_server_name]
```

### 2. MCP Servers Configuration
Configure how nanobot connects to your MCP server:

```yaml
mcpServers:
  your_mcp_server_name:
    command: "/full/path/to/executable"
    args: ["arg1", "arg2"]
    env:
      LOG_LEVEL: info
      # Other environment variables
```

**Important**: Use absolute paths and separate command from arguments.

### 3. Complete Example

```yaml
agents:
  openapi_assistant:
    name: OpenAPI Navigator Assistant
    model: claude-sonnet-4-20250514
    description: |
      I help explore and interact with OpenAPI specifications. I can:
      - Load OpenAPI specs from files or URLs
      - Search endpoints and schemas with pagination
      - Get detailed or summary views of endpoints
      - Make actual API requests to test endpoints
    mcpServers: [openapi_navigator]

mcpServers:
  openapi_navigator:
    command: /Users/username/.cargo/bin/uv
    args: ["run", "openapi-navigator"]
    env:
      LOG_LEVEL: info
```

## Running the Demo

1. **Start nanobot**:
   ```bash
   nanobot run path/to/nanobot.yaml
   ```

2. **Access the demo**:
   - Open http://localhost:8080 in your browser
   - Start chatting with your AI agent
   - The agent will automatically use your MCP server's tools

## Best Practices

### Model Selection
- **Claude Sonnet 4**: Use `claude-sonnet-4-20250514` (latest stable)
- **GPT-4**: Use `gpt-4` or `gpt-4-turbo`
- Always verify model names in your provider's documentation

### Environment Management
- Keep API keys in `.env` files, never in configuration
- Add `.env` to `.gitignore`
- Use environment variables for sensitive configuration

### MCP Server Configuration
- Use absolute paths for commands (e.g., `/Users/username/.cargo/bin/uv`)
- Separate command and arguments properly
- Set appropriate working directory if needed with `cwd` parameter
- Use `LOG_LEVEL: info` for debugging

### Makefile Integration
Create a make target for easy demo launching:

```makefile
demo:  ## Start nanobot demo
	@echo "Starting demo..."
	@echo "Demo will be available at http://localhost:8080"
	@if [ -f .env ]; then \
		set -a && source .env && set +a && nanobot run ./demo/nanobot.yaml; \
	else \
		echo "Error: .env file not found. Please create .env with API keys"; \
		exit 1; \
	fi
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Kill existing nanobot processes or use a different port
2. **Model not found**: Verify model name with your AI provider
3. **MCP server startup failed**: Check command paths and arguments
4. **API key issues**: Ensure `.env` file is properly formatted and sourced

### Debugging Steps

1. **Check nanobot logs**: Look for error messages in terminal output
2. **Verify MCP server**: Test your MCP server independently
3. **Test API keys**: Verify keys work with direct API calls
4. **Validate YAML**: Ensure configuration file is valid YAML

## Demo Flow

1. **Introduction**: Start with a brief explanation of what the MCP server does
2. **Basic functionality**: Demonstrate core features step by step
3. **Advanced features**: Show pagination, filtering, complex operations
4. **Real-world usage**: Use actual APIs or realistic data
5. **Error handling**: Show how the system handles errors gracefully

This approach provides stakeholders with an interactive, visual demonstration of your MCP server's capabilities without requiring technical setup.
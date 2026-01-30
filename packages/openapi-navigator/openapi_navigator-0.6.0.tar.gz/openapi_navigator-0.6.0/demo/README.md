# OpenAPI Navigator Demo

This directory contains configuration for demonstrating OpenAPI Navigator functionality using various tools.

## Quick Demo with Nanobot.ai

Nanobot provides an easy way to create interactive demos of MCP servers with a web UI.

### Setup

1. **Install nanobot:**
   ```bash
   npm install -g @nanobot-ai/nanobot
   ```

2. **Set API keys:**
   ```bash
   export OPENAI_API_KEY=sk-...
   # OR
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

3. **Run the demo:**
   ```bash
   # From project root
   nanobot run demo/nanobot.yaml
   ```

4. **Access the demo:**
   Open http://localhost:8080 in your browser

### Demo Features

The demo creates an interactive assistant that can:
- Load OpenAPI specifications from files or URLs
- Search endpoints and schemas with new pagination features
- Get detailed or summary-only endpoint information
- Make actual API requests to test endpoints

### Example Demo Flow

1. Load a spec: "Load the OpenAPI spec from https://petstore.swagger.io/v2/swagger.json"
2. Explore endpoints: "Show me all the endpoints with pagination, limit 5"
3. Get endpoint details: "Get the summary-only view of the POST /pet endpoint"
4. Test an endpoint: "Make a GET request to the /pet/findByStatus endpoint with status=available"

## MCP Inspector Testing

For development and testing, use the MCP Inspector:

```bash
# Interactive UI mode
npx @modelcontextprotocol/inspector uv run openapi-navigator

# CLI mode for automation
npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/list
```

## Sample OpenAPI Specs for Testing

- **Petstore v2 (Swagger):** https://petstore.swagger.io/v2/swagger.json
- **Petstore v3 (OpenAPI):** https://petstore3.swagger.io/api/v3/openapi.json
- **JSONPlaceholder:** https://jsonplaceholder.typicode.com/
- **GitHub API:** https://docs.github.com/en/rest

## Testing New Features

The demo environment is perfect for testing our new features:

1. **Pagination:** Try "Search for endpoints with 'user' in the name, limit to 3 results"
2. **Summary Mode:** Try "Get the summary-only view of an endpoint to reduce token usage"
3. **API Requests:** Try "Make a test request to verify the endpoint works"
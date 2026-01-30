# OpenAPI Navigator

<!-- mcp-name: io.github.mgaruccio/openapi-navigator -->

[![CI](https://github.com/mikegaruccio/openapi-navigator/workflows/CI/badge.svg)](https://github.com/mikegaruccio/openapi-navigator/actions/workflows/ci.yml)
[![Build](https://github.com/mikegaruccio/openapi-navigator/workflows/Build/badge.svg)](https://github.com/mikegaruccio/openapi-navigator/actions/workflows/build.yml)
[![Release](https://github.com/mikegaruccio/openapi-navigator/workflows/Release/badge.svg)](https://github.com/mikegaruccio/openapi-navigator/actions/workflows/release.yml)

An MCP (Model Context Protocol) server that provides tools for navigating and querying OpenAPI specifications. This server makes it easy for AI agents to explore, search, and understand OpenAPI specs without having to manually parse complex JSON/YAML files.

## Features

- **Load OpenAPI specs** from local files or URLs
- **Navigate endpoints** with filtering by tags
- **Search endpoints** using fuzzy matching across paths, summaries, and operation IDs with **pagination support**
- **Explore schemas** and their definitions with **pagination support**
- **Summary-only views** - get condensed endpoint information to reduce token usage
- **API interaction** - make direct REST API calls to test endpoints
- **Multiple spec support** - load and manage multiple OpenAPI specifications simultaneously
- **Smart indexing** for fast lookups and searches
- **Reference preservation** - maintains `$ref` structures for agents to decide when to resolve
- **Comprehensive demo environment** - interactive testing with Nanobot and MCP Inspector

## Installation

The OpenAPI Navigator is available on PyPI and can be installed using `uvx` (recommended) or `pip`:

```bash
# Using uvx (recommended)
uvx openapi-navigator

# Or install globally with pip
pip install openapi-navigator
```

## Usage

### MCP Configuration

Add the OpenAPI Navigator to your MCP client configuration:

#### For Cursor
Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "openapi-navigator": {
      "command": "uvx",
      "args": ["openapi-navigator"],
      "env": {}
    }
  }
}
```

#### For Claude Desktop
Add to your Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "openapi-navigator": {
      "command": "uvx",
      "args": ["openapi-navigator"],
      "env": {}
    }
  }
}
```

#### For Code
Add to your Code MCP configuration:

```json
{
  "mcpServers": {
    "openapi-navigator": {
      "command": "uvx",
      "args": ["openapi-navigator"],
      "env": {}
    }
  }
}
```

## Available Tools

The OpenAPI Navigator provides the following tools:

### Core Operations
- **`load_spec`** - Load an OpenAPI specification from a local file (requires absolute path)
- **`load_spec_from_url`** - Load an OpenAPI specification from a URL
- **`list_loaded_specs`** - List all currently loaded specifications
- **`unload_spec`** - Remove a specification from memory

### Endpoint Operations
- **`search_endpoints`** - Search endpoints using fuzzy matching with pagination support. Use `""` or `"a"` as the query to get all endpoints
  - Parameters: `spec_id`, `query`, `limit` (max 200), `offset` (default 0)
- **`get_endpoint`** - Get detailed information for a specific endpoint by path and method
  - Parameters: `spec_id`, `path`, `method`, `summary_only` (boolean, default false)

### Schema Operations
- **`search_schemas`** - Search schema names using fuzzy matching with pagination support. Use `""` or `"a"` as the query to get all schemas
  - Parameters: `spec_id`, `query`, `limit` (max 200), `offset` (default 0)
- **`get_schema`** - Get detailed information for a specific schema by name
- **`get_spec_metadata`** - Get comprehensive metadata about a loaded OpenAPI specification

### Header Management
- **`set_spec_headers`** - Mount authentication or other headers to a loaded spec. Headers are automatically applied when using `make_api_request` with the `spec_id` parameter.
  - Parameters: `spec_id`, `headers` (object, optional)

### API Interaction
- **`make_api_request`** - Make direct REST API calls to test endpoints
  - Parameters: `url`, `method` (GET/POST/PUT/PATCH/DELETE/etc.), `headers`, `params`, `data`, `timeout`, `spec_id` (optional)

## Tool Documentation

### `set_spec_headers`

Mount authentication or other headers to a loaded spec. Headers are automatically applied when using `make_api_request` with the `spec_id` parameter.

**Parameters:**
- `spec_id` (string): ID of the loaded spec
- `headers` (object, optional): Dictionary of HTTP headers

**Example:**
```json
{
  "spec_id": "my-api",
  "headers": {
    "Authorization": "Bearer secret-token-12345",
    "X-API-Key": "api-key-67890"
  }
}
```

**Use Case:**
```
// Load your API spec
load_spec_from_url("https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json", "github-api")

// Mount your auth token once
set_spec_headers("github-api", {"Authorization": "Bearer ghp_your_token"})

// Make requests without repeating auth
make_api_request("https://api.github.com/user", spec_id="github-api")
make_api_request("https://api.github.com/user/repos", spec_id="github-api")
```

### `make_api_request`

Make HTTP requests to REST APIs.

**Parameters:**
- `url` (string): Full URL to request
- `method` (string, optional): HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS). Default: "GET"
- `headers` (object, optional): HTTP headers dictionary
- `params` (object, optional): URL parameters dictionary
- `data` (string, optional): Request body as string
- `timeout` (integer, optional): Timeout in seconds. Default: 30
- `spec_id` (string, optional): Load default headers from this spec. Request headers override spec headers.

**Example with spec_id:**
```json
{
  "url": "https://api.example.com/users",
  "spec_id": "my-api",
  "headers": {
    "X-Custom-Header": "custom-value"
  }
}
```

This merges headers from `set_spec_headers("my-api")` with `X-Custom-Header`, with request headers taking precedence.

## Example Workflow

1. **Load a specification:**
   ```
   load_spec("/absolute/path/to/schema.yaml", "my-api")
   ```

2. **Get all endpoints with pagination:**
   ```
   search_endpoints("my-api", "", 50, 0)  # First 50 endpoints
   search_endpoints("my-api", "", 50, 50) # Next 50 endpoints
   ```

3. **Get all schemas:**
   ```
   search_schemas("my-api", "")
   ```

4. **Search for specific endpoints:**
   ```
   search_endpoints("my-api", "virtual machine")
   ```

5. **Get endpoint details (summary view):**
   ```
   get_endpoint("my-api", "/api/virtualization/virtual-machines/", "GET", true)
   ```

6. **Get full endpoint details:**
   ```
   get_endpoint("my-api", "/api/virtualization/virtual-machines/", "GET", false)
   ```

7. **Get schema details:**
   ```
   get_schema("my-api", "VirtualMachine")
   ```

8. **Mount authentication headers to a spec:**
   ```
   set_spec_headers("my-api", {"Authorization": "Bearer secret-token"})
   ```

9. **Test an API endpoint (with mounted headers):**
   ```
   make_api_request("https://api.example.com/users", spec_id="my-api")
   ```

10. **Override headers for a specific request:**
    ```
    make_api_request("https://api.example.com/admin", spec_id="my-api", headers={"X-Admin-Token": "admin-token"})
    ```

11. **Get spec metadata:**
    ```
    get_spec_metadata("my-api")
    ```

## Demo Environment

The OpenAPI Navigator includes a comprehensive demo environment for interactive testing and development.

### Nanobot Integration

Run the interactive demo using Nanobot (requires installation):

```bash
# Install nanobot
brew install nanobot-ai/tap/nanobot

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Start the demo
make demo
```

The demo will be available at `http://localhost:8080` and provides a web interface for testing OpenAPI Navigator features.

### MCP Inspector Integration

#### Web UI Inspector
```bash
make inspect
```
Opens MCP Inspector web UI at `http://localhost:6274` for interactive tool testing.

#### CLI Inspector
```bash
make inspect-cli
```
Lists all available tools via command line.

#### Automated Inspector Tests
```bash
make test-inspector
```
Runs automated tests using MCP Inspector CLI to validate tool functionality.

## Development

### Testing

The OpenAPI Navigator includes a comprehensive test suite with both unit and integration tests.

#### Running Tests

**All tests:**
```bash
uv run pytest
```

**Unit tests only (fast):**
```bash
uv run pytest tests/unit/
```

**Integration tests only:**
```bash
uv run pytest tests/integration/
```

**With coverage report:**
```bash
uv run pytest --cov=src --cov-report=html
```

#### Using the Makefile

For convenience, a Makefile is provided with common test targets:

```bash
# Run all tests
make test

# Run only unit tests (fast feedback)
make test-unit

# Run integration tests
make test-integration

# Run tests with coverage report
make test-cov

# Clean up generated files
make clean

# Format code
make format

# Lint code
make lint
```

#### Test Structure

- **`tests/unit/`** - Unit tests for individual components
  - `test_spec_manager.py` - Tests for the core specification management
- **`tests/integration/`** - Integration tests for complete workflows
  - `test_integration.py` - End-to-end workflow testing
- **`tests/conftest.py`** - Shared test fixtures and configuration

#### Test Coverage

The test suite aims for at least 65% code coverage and includes:
- **31 unit tests** covering core functionality
- **5 integration tests** covering complete workflows
- **Mock testing** for external dependencies
- **Error handling** validation
- **Edge case** coverage

### Inspecting the Server

Use FastMCP CLI to inspect the server:
```bash
uvx fastmcp inspect openapi-navigator
```

This will generate a `server-info.json` file with detailed information about all available tools.

## CI/CD Pipeline

The OpenAPI Navigator uses GitHub Actions for continuous integration and deployment.

### Workflows

#### 🔄 **CI** (`ci.yml`)
- **Triggers**: Pull requests and pushes to main
- **Runs**: Tests on Python 3.10, 3.11, and 3.12
- **Features**:
  - Full test suite execution
  - Code coverage reporting
  - Linting and formatting checks with ruff
  - Code formatting with black

#### 🏗️ **Build** (`build.yml`)
- **Triggers**: Merges to main branch
- **Features**:
  - Comprehensive testing
  - Package building
  - Code quality checks
  - Artifact uploads

#### 🚀 **Release** (`release.yml`)
- **Triggers**: GitHub releases
- **Features**:
  - Automatic PyPI publishing (supports trusted publisher OIDC)
  - GitHub release creation
  - Pre-release testing

#### 📦 **Dependencies** (`dependencies.yml`)
- **Triggers**: Weekly (Mondays) + manual
- **Features**:
  - Automatic dependency updates
  - Pull request creation
  - Test validation

### Setup Requirements

#### **Option 1: Trusted Publisher (Recommended)**
1. **PyPI Account**: Create account at [pypi.org](https://pypi.org)
2. **Configure Trusted Publisher**: In PyPI settings, add GitHub as a trusted publisher
3. **Push to GitHub**: Workflows will automatically activate

#### **Option 2: API Token (Traditional)**
1. **PyPI Account**: Create account at [pypi.org](https://pypi.org)
2. **Generate API Token**: In PyPI settings, create an API token
3. **GitHub Secrets**: Add `PYPI_API_TOKEN` with your PyPI token
4. **Update Workflow**: Uncomment the `UV_TOKEN` line in `.github/workflows/release.yml`
5. **Push to GitHub**: Workflows will automatically activate

### Release Process

1. **Create Release**: Tag a new version in GitHub
2. **Automated Testing**: CI runs full test suite
3. **Package Building**: Creates distributable packages
4. **PyPI Publishing**: Automatically publishes to PyPI
5. **Release Notes**: Generates comprehensive release notes

### Quality Gates

- ✅ **Test Coverage**: Minimum 65% required
- ✅ **All Tests Pass**: Unit and integration tests
- ✅ **Code Quality**: Linting and formatting with ruff and black
- ✅ **Dependencies**: Up-to-date and secure

## Architecture

The OpenAPI Navigator consists of two main components:

1. **SpecManager**: Handles loading, validation, and indexing of OpenAPI specifications
2. **MCP Server**: Exposes tools through the Model Context Protocol

### SpecManager Features

- **Multi-format support**: Handles both YAML and JSON OpenAPI specs
- **Version detection**: Automatically detects OpenAPI 3.x vs Swagger 2.x
- **Smart indexing**: Builds indexes for fast endpoint and schema lookups
- **Fuzzy search**: Provides intelligent search across endpoint metadata
- **Reference handling**: Preserves `$ref` structures without automatic resolution

### Error Handling

- **Validation warnings**: Warns on validation issues but continues if possible
- **Graceful degradation**: Only rejects specs that prevent core functionality
- **Helpful error messages**: Provides clear feedback on what went wrong

## Security Considerations

- **Absolute paths only**: Local file loading requires absolute paths for security
- **No automatic execution**: The server only reads and parses specs, never executes code
- **Input validation**: All inputs are validated before processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenAPI Navigator is a Model Context Protocol (MCP) server that provides tools for navigating and querying OpenAPI specifications. The project consists of three main Python modules:

- **`spec_manager.py`** - Core specification management with the `SpecManager` class and `OpenAPISpec` class
- **`server.py`** - FastMCP server implementation with MCP tool definitions
- **`__init__.py`** - Package initialization and exports

## Development Commands

### Testing
```bash
# Run all tests
uv run pytest
make test

# Run unit tests only (fast feedback)
uv run pytest tests/unit/
make test-unit

# Run integration tests only
uv run pytest tests/integration/
make test-integration

# Run MCP integration tests only
uv run pytest tests/mcp/
make test-mcp

# Run tests with coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term-missing
make test-cov

# Run fast tests (exclude slow markers)
uv run pytest -m "not slow"
make test-fast
```

### Code Quality
```bash
# Format code with black
uv run black src/ tests/
make format

# Lint code with ruff (checking and formatting)
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
make lint
```

### Build and Run
```bash
# Install development dependencies
uv sync
make install-dev

# Build the package
uv build
make build

# Run the OpenAPI Navigator server
uv run openapi-navigator
make run
```

### Demo and Development
```bash
# Start interactive demo with Nanobot
make demo

# Open MCP Inspector web UI
make inspect

# Run MCP Inspector CLI
make inspect-cli

# Run automated inspector tests
make test-inspector
```

### Cleanup
```bash
# Clean up generated files
make clean
```

## Architecture

### Core Components

**SpecManager Class** (`spec_manager.py:151+`):
- Manages multiple OpenAPI specifications in memory
- Handles loading from files and URLs with robust format detection
- Provides fuzzy search capabilities across endpoints and schemas
- Maintains a registry of loaded specs by ID

**OpenAPISpec Class** (`spec_manager.py:14-150`):
- Represents individual OpenAPI/Swagger specifications 
- Auto-detects OpenAPI 3.x vs Swagger 2.x versions
- Builds fast lookup indexes for endpoints and schemas during initialization
- Handles both OpenAPI 3.x (`components/schemas`) and Swagger 2.x (`definitions`) schema locations

**MCP Server** (`server.py`):
- Exposes 11 MCP tools: `load_spec`, `load_spec_from_url`, `list_loaded_specs`, `unload_spec`, `search_endpoints`, `get_endpoint`, `search_schemas`, `get_schema`, `get_spec_metadata`, `set_spec_headers`, `make_api_request`
- Uses FastMCP framework for tool registration
- Maintains global `_spec_manager` instance shared across all tools
- Supports pagination for `search_endpoints` and `search_schemas` with `limit` (max 200) and `offset` parameters
- Provides summary-only mode for `get_endpoint` to reduce token usage

**Header Mounting** (`server.py`):
- `set_spec_headers` tool mounts default headers to a loaded spec
- Headers stored in `OpenAPISpec.default_headers` dictionary
- `make_api_request` accepts optional `spec_id` parameter to auto-apply headers
- Request headers override spec headers when both present (precedence model)
- Eliminates need for agents to pass auth headers on every request

### Format Detection Strategy

The codebase implements a robust format detection strategy (`spec_manager.py:309-340`):
1. Content-based detection using OpenAPI/Swagger keywords
2. Structural analysis (JSON braces vs YAML syntax) 
3. Defaults to YAML parsing as it's more permissive

### Search and Indexing

- **Fuzzy Search**: Uses `fuzzywuzzy` library for intelligent matching across endpoint paths, summaries, and operation IDs
- **Fast Indexing**: Pre-builds endpoint and schema indexes during spec loading for O(1) lookups
- **Reference Preservation**: Maintains `$ref` structures without automatic resolution, letting agents decide when to resolve
- **Pagination Support**: Search operations support `limit` and `offset` parameters for handling large datasets efficiently
- **Summary-Only Views**: Endpoints can return condensed information to reduce token usage with `summary_only` parameter

## API Request Tool

The `make_api_request` tool (`server.py:195-310`) enables direct REST API interaction:

**Features:**
- Supports all HTTP methods: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- Accepts custom headers, URL parameters, and request body data
- Returns structured response with status, headers, body, JSON (if applicable), timing
- Comprehensive error handling for timeouts, connection errors, and validation
- Automatic JSON parsing when possible

**Usage:**
```python
make_api_request(
    url="https://api.example.com/endpoint",
    method="POST",
    headers={"Content-Type": "application/json"},
    params={"param": "value"}, 
    data='{"key": "value"}',
    timeout=30
)
```

## Testing Structure

- **Unit Tests** (`tests/unit/`):
  - `test_spec_manager.py` - 31 tests covering core SpecManager functionality
  - `test_api_request.py` - 25+ tests covering make_api_request functionality
- **Integration Tests** (`tests/integration/`):
  - `test_integration.py` - 5 end-to-end workflow tests
  - `test_api_request_integration.py` - 10 real API integration tests using httpbin.org
- **MCP Integration Tests** (`tests/mcp/`):
  - `test_mcp_integration.py` - 20+ tests covering MCP protocol layer, pagination, and summary features
- **Header Mounting Tests**:
  - Unit tests for `set_spec_headers` and header merging logic
  - MCP integration tests validating end-to-end header mounting workflow
  - Real HTTP tests using httpbin.org to verify headers are sent correctly
- **Test Configuration** - pytest with asyncio support, 65% coverage requirement
- **Fixtures** (`tests/conftest.py`) - Shared test utilities and mock data

## Dependencies

**Core Runtime**:
- `fastmcp` - MCP server framework
- `pyyaml` - YAML parsing
- `requests` - HTTP client for URL loading
- `fuzzywuzzy` + `python-levenshtein` - Fuzzy searching
- `jsonschema` - OpenAPI validation

**Development**:
- `pytest` ecosystem for testing
- `black` for code formatting  
- `ruff` for linting and additional formatting
- `uv` for dependency management

## Project Structure Notes

- Entry point is `openapi_navigator:main` (via `server.py:main()`)
- All source code in `src/openapi_navigator/`
- Package uses modern `pyproject.toml` configuration
- CI/CD via GitHub Actions with Python 3.10-3.12 matrix testing
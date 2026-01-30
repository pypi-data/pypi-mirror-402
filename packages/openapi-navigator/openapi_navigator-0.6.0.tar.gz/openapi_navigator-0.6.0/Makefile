.PHONY: help test test-unit test-integration test-mcp test-cov test-fast clean format lint demo inspect inspect-cli test-inspector

help:  ## Show this help message
	@echo "OpenAPI Navigator - Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

test:  ## Run all tests
	uv run pytest

test-unit:  ## Run only unit tests (fast)
	uv run pytest tests/unit/ -v

test-integration:  ## Run only integration tests
	uv run pytest tests/integration/ -v

test-mcp:  ## Run MCP integration tests
	uv run pytest tests/mcp/ -v

test-cov:  ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

test-fast:  ## Run fast tests (exclude slow markers)
	uv run pytest -m "not slow"

clean:  ## Clean up generated files
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf src/openapi_mcp/__pycache__/
	rm -rf tests/__pycache__/
	rm -rf tests/unit/__pycache__/
	rm -rf tests/integration/__pycache__/

format:  ## Format code with black
	uv run black src/ tests/

lint:  ## Lint code with ruff
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

install-dev:  ## Install development dependencies
	uv sync

build:  ## Build the package
	uv build

install:  ## Install the package in development mode
	uv sync

run:  ## Run the OpenAPI Navigator server
	uv run openapi-navigator

demo:  ## Start nanobot demo (requires: brew install nanobot-ai/tap/nanobot and .env file)
	@echo "Starting OpenAPI Navigator demo..."
	@echo "Demo will be available at http://localhost:8080"
	@if [ -f .env ]; then \
		set -a && source .env && set +a && nanobot run ./demo/nanobot.yaml --default-model claude-sonnet-4-20250514; \
	else \
		echo "Error: .env file not found. Please create .env with ANTHROPIC_API_KEY=your-key"; \
		exit 1; \
	fi

inspect:  ## Start MCP Inspector web UI
	@echo "Starting MCP Inspector web UI..."
	@echo "Inspector will be available at http://localhost:6274"
	npx @modelcontextprotocol/inspector uv run openapi-navigator

inspect-cli:  ## Run MCP Inspector in CLI mode (list tools)
	@echo "Running MCP Inspector CLI to list tools..."
	npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/list

test-inspector:  ## Run automated MCP Inspector tests (CLI mode - single operations only)
	@echo "Testing OpenAPI Navigator with MCP Inspector CLI..."
	@echo "Note: Each CLI call creates a new server instance, so state doesn't persist"
	@echo ""
	@echo "1. Listing available tools..."
	npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/list | head -20
	@echo ""
	@echo "2. Loading petstore OpenAPI spec (single operation test)..."
	npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/call \
		--tool-name load_spec_from_url \
		--tool-arg spec_id=petstore \
		--tool-arg url=https://petstore3.swagger.io/api/v3/openapi.json
	@echo ""
	@echo "3. Testing API request tool..."
	npx @modelcontextprotocol/inspector --cli uv run openapi-navigator --method tools/call \
		--tool-name make_api_request \
		--tool-arg url=https://httpbin.org/get \
		--tool-arg method=GET
	@echo ""
	@echo "MCP Inspector CLI tests completed!"
	@echo "For persistent state testing, use 'make inspect' for web UI or 'make test-mcp' for FastMCP tests"

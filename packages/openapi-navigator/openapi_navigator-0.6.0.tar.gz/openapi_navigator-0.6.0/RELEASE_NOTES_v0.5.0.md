# OpenAPI Navigator v0.5.0 - Header Mounting Release

**Release Date:** 2025-11-14

## 🎉 New Features

### Header Mounting for API Authentication

This release adds the ability to "mount" authentication headers to loaded OpenAPI specs, eliminating the need to pass headers on every request.

#### New MCP Tool: `set_spec_headers`

```json
// Mount auth headers once
{
  "spec_id": "my-api",
  "headers": {
    "Authorization": "Bearer secret-token",
    "X-API-Key": "api-key-123"
  }
}
```

#### Enhanced: `make_api_request`

New optional `spec_id` parameter automatically applies mounted headers:

```json
// Headers automatically applied from spec
{
  "url": "https://api.example.com/users",
  "spec_id": "my-api"
}

// Override specific headers while keeping others
{
  "url": "https://api.example.com/admin",
  "spec_id": "my-api",
  "headers": {"X-Admin-Token": "admin-override"}
}
```

## 🔧 Technical Details

- **Header Storage**: Headers stored in `OpenAPISpec.default_headers` dictionary
- **Header Merging**: Request headers override spec headers (precedence model)
- **Multiple Specs**: Each loaded spec maintains its own header set independently
- **Type Safety**: Full type hints for all new parameters

## 📚 Documentation

- Updated README.md with header mounting examples
- Enhanced CLAUDE.md with architecture details
- Added real-world GitHub API example

## ✅ Testing

- 15+ new unit tests for header storage and merging
- 4 new MCP integration tests
- 2 end-to-end workflow tests using real APIs
- All tests passing with >65% coverage

## 🎯 Use Cases

**Before (v0.4.0):**
```json
make_api_request("/users", headers: {"Authorization": "Bearer token"})
make_api_request("/posts", headers: {"Authorization": "Bearer token"})
make_api_request("/comments", headers: {"Authorization": "Bearer token"})
```

**After (v0.5.0):**
```json
set_spec_headers("my-api", {"Authorization": "Bearer token"})
make_api_request("/users", spec_id: "my-api")
make_api_request("/posts", spec_id: "my-api")
make_api_request("/comments", spec_id: "my-api")
```

## 🔗 Related Issues

Resolves issue where AI agents repeatedly passed authentication headers on every API request, leading to verbose prompts and potential security concerns.

## 📦 Installation

```bash
pip install openapi-navigator==0.5.0
# or
uv add openapi-navigator==0.5.0
```

## 🙏 Acknowledgments

Feature requested by AI agent developers experiencing header repetition fatigue.

---

**Full Changelog**: v0.4.0...v0.5.0

# OpenAPI Navigator - Marketing Materials

## 📝 Descriptions

### Ultra-Short (Tweet/Tag - ~140 chars)
```
MCP server for navigating OpenAPI specs with fuzzy search, pagination, header mounting, and direct API testing. Supports OpenAPI 3.x & Swagger 2.x
```

### Short (1-2 sentences - ~200 chars)
```
MCP server for navigating and querying OpenAPI specifications with 11 powerful tools including fuzzy search, schema inspection, header mounting for authentication, and direct API testing capabilities.
```

### Medium (Detailed - ~400 chars)
```
OpenAPI Navigator is a Model Context Protocol (MCP) server that enables AI agents to explore, search, and interact with OpenAPI specifications effortlessly. Features include fuzzy search across endpoints and schemas with pagination, summary-only views for token efficiency, header mounting for streamlined authentication, and direct REST API testing. Supports both OpenAPI 3.x and Swagger 2.x formats with smart indexing for fast lookups.
```

### Long (Comprehensive)
```
OpenAPI Navigator is a production-ready MCP server that provides AI agents with 11 specialized tools for navigating and querying OpenAPI specifications. It eliminates the need for agents to manually parse complex JSON/YAML files by providing:

• Smart loading from local files or URLs with auto-detection of OpenAPI 3.x vs Swagger 2.x
• Fuzzy search across endpoints and schemas with configurable pagination (up to 200 results per page)
• Summary-only views to reduce token usage for large APIs
• Header mounting system for authentication - set headers once, use across multiple requests
• Direct REST API testing with support for all HTTP methods
• Multi-spec management - load and query multiple API specifications simultaneously
• Reference preservation - maintains $ref structures for intelligent resolution
• Comprehensive error handling and validation

Built with FastMCP on Python 3.10+, OpenAPI Navigator is available on PyPI with easy installation via uvx. It includes 65+ tests with integration testing, CI/CD via GitHub Actions, and comprehensive documentation.

Perfect for AI agents working with REST APIs, API documentation exploration, automated testing, and multi-API workflows.
```

---

## 🎯 Categories

**Primary**: Development Tools / API Tools
**Secondary**: Productivity, Infrastructure, Testing

---

## 🏷️ Tags/Keywords

```
openapi, swagger, api, rest, mcp, model-context-protocol, fuzzy-search,
api-testing, api-documentation, schema, endpoints, authentication,
developer-tools, python, fastmcp, ai-tools
```

---

## 📊 Key Features (Bullet Points)

### Core Features
- ✅ Load OpenAPI specs from local files or URLs
- ✅ Fuzzy search across endpoints with pagination (up to 200 results)
- ✅ Schema exploration with intelligent search
- ✅ Summary-only views for token efficiency
- ✅ Header mounting for streamlined authentication
- ✅ Direct REST API testing (GET, POST, PUT, PATCH, DELETE, etc.)
- ✅ Multi-spec management - work with multiple APIs simultaneously
- ✅ Auto-detection of OpenAPI 3.x vs Swagger 2.x
- ✅ Smart indexing for O(1) lookups
- ✅ Reference preservation with $ref structures
- ✅ Comprehensive error handling and validation

### Technical Highlights
- 🐍 Python 3.10+ with FastMCP framework
- 📦 Available on PyPI - install with `uvx openapi-navigator`
- ✅ 65+ tests with unit, integration, and MCP protocol testing
- 🔄 CI/CD with GitHub Actions
- 📚 Comprehensive documentation and examples
- 🚀 Production-ready with robust error handling

---

## 📋 Submission Templates

### Template A: MCPServers.org Form

**Server Name:**
```
OpenAPI Navigator
```

**Short Description:**
```
MCP server for navigating and querying OpenAPI specifications with fuzzy search, schema inspection, header mounting for authentication, and direct API testing capabilities.
```

**Link:**
```
https://github.com/mikegaruccio/openapi-navigator
```

**Category:**
```
development
```

**Contact Email:**
```
mike.garuccio@expedient.com
```

---

### Template B: Official MCP Registry - server.json

Create this in your project root before running `mcp-publisher init`:

```json
{
  "name": "openapi-navigator",
  "displayName": "OpenAPI Navigator",
  "description": "MCP server for navigating and querying OpenAPI specifications with fuzzy search, pagination, header mounting, and API testing",
  "author": "Mike Garuccio",
  "homepage": "https://github.com/mikegaruccio/openapi-navigator",
  "license": "MIT",
  "keywords": [
    "openapi",
    "swagger",
    "api",
    "rest",
    "fuzzy-search",
    "api-testing",
    "developer-tools"
  ],
  "categories": [
    "development",
    "api-tools",
    "productivity"
  ],
  "package": {
    "type": "pypi",
    "name": "openapi-navigator"
  }
}
```

**README marker for PyPI:**
Add this to your README.md (already present):
```markdown
<!-- mcp-name: openapi-navigator -->
```

---

### Template C: Awesome MCP Servers Pull Request

**PR Title:**
```
Add OpenAPI Navigator - API specification navigation and testing
```

**PR Description:**
```
# OpenAPI Navigator

**Category:** Development Tools / API Tools

**Description:** MCP server for navigating and querying OpenAPI specifications with 11 specialized tools including fuzzy search, pagination, header mounting for authentication, and direct REST API testing.

**Links:**
- GitHub: https://github.com/mikegaruccio/openapi-navigator
- PyPI: https://pypi.org/project/openapi-navigator/
- Installation: `uvx openapi-navigator`

**Key Features:**
- Load OpenAPI specs from files or URLs (supports OpenAPI 3.x & Swagger 2.x)
- Fuzzy search across endpoints and schemas with pagination
- Summary-only views to reduce token usage
- Header mounting for streamlined authentication
- Direct REST API testing with all HTTP methods
- Multi-spec management
- 65+ tests with CI/CD
```

**Entry to add to README (under appropriate category):**
```markdown
- [OpenAPI Navigator](https://github.com/mikegaruccio/openapi-navigator) - Navigate and query OpenAPI specifications with fuzzy search, pagination, header mounting, and API testing. Supports OpenAPI 3.x & Swagger 2.x.
```

---

### Template D: Reddit/HackerNews Post

**Title:**
```
OpenAPI Navigator - MCP server for navigating and testing REST APIs
```

**Post:**
```
I built OpenAPI Navigator, an MCP (Model Context Protocol) server that makes it easy for AI agents to work with OpenAPI specifications.

**What it does:**
Instead of AI agents struggling to parse complex OpenAPI/Swagger YAML/JSON files, they can use 11 specialized tools to:
- Load specs from files or URLs
- Fuzzy search across endpoints and schemas
- Get condensed summaries to save tokens
- Mount authentication headers once and reuse them
- Test API endpoints directly with any HTTP method

**Why I built it:**
Working with large API specifications (hundreds of endpoints) was painful for AI agents. They'd hit token limits, struggle with pagination, and have to repeatedly pass auth headers. OpenAPI Navigator solves these problems.

**Technical details:**
- Python 3.10+ with FastMCP
- Available on PyPI: `uvx openapi-navigator`
- 65+ tests with full CI/CD
- Supports both OpenAPI 3.x and Swagger 2.x
- Production-ready with comprehensive error handling

**Example workflow:**
1. Load your API spec
2. Mount your auth token once with `set_spec_headers`
3. Search endpoints with fuzzy matching
4. Test endpoints directly - headers auto-applied
5. Explore schemas and documentation

GitHub: https://github.com/mikegaruccio/openapi-navigator
PyPI: https://pypi.org/project/openapi-navigator/

Happy to answer questions or hear feedback!
```

---

### Template E: Twitter/X Thread

**Tweet 1:**
```
🚀 Just released OpenAPI Navigator - an MCP server that makes working with OpenAPI specs 10x easier for AI agents

✅ Fuzzy search endpoints & schemas
✅ Header mounting for auth
✅ Direct API testing
✅ Pagination & token optimization

pip install openapi-navigator

🧵 1/5
```

**Tweet 2:**
```
Problem: AI agents struggle with large OpenAPI specs - token limits, manual parsing, repeated auth headers

Solution: 11 specialized tools that handle the complexity:
- Smart loading (files or URLs)
- Intelligent search
- Summary views
- Header management

2/5
```

**Tweet 3:**
```
Example: Testing the GitHub API

1. Load spec from URL
2. Mount your auth token ONCE
3. Search for endpoints with fuzzy matching
4. Test multiple endpoints - auth auto-applied

No more copying auth headers everywhere! 🎉

3/5
```

**Tweet 4:**
```
Built with:
🐍 Python 3.10+ & FastMCP
📦 Available on PyPI
✅ 65+ tests
🔄 Full CI/CD
📚 Comprehensive docs

Supports both OpenAPI 3.x and Swagger 2.x with auto-detection

4/5
```

**Tweet 5:**
```
Install: uvx openapi-navigator

GitHub: github.com/mikegaruccio/openapi-navigator
PyPI: pypi.org/project/openapi-navigator/

Perfect for:
- API exploration
- Automated testing
- Multi-API workflows
- Documentation discovery

Let me know what you think! 🚀

5/5
```

---

## 📸 Visual Assets (Suggested)

### Demo GIF/Video Ideas
1. **Quick start**: Load spec → Search endpoints → Test API call
2. **Header mounting workflow**: Set headers once → Multiple requests
3. **Pagination demo**: Search large API → Paginate through results
4. **Multi-spec management**: Load multiple APIs → Switch between them

### Screenshots to Create
1. **MCP Inspector UI** showing available tools
2. **Nanobot demo** interacting with OpenAPI Navigator
3. **Terminal output** showing successful API test
4. **Code snippet** of MCP configuration

---

## 🎤 Elevator Pitch (30 seconds)

```
OpenAPI Navigator is an MCP server that gives AI agents superpowers for working with REST APIs.

Instead of struggling with complex OpenAPI files, agents get 11 specialized tools: fuzzy search across endpoints and schemas, header mounting so you set auth once and forget it, direct API testing, and smart pagination for large APIs.

It's production-ready, available on PyPI, and takes 30 seconds to install with uvx. Perfect for anyone building AI agents that need to interact with REST APIs.
```

---

## 💡 Value Propositions

### For AI Agent Developers
- **Reduce complexity**: No manual OpenAPI parsing
- **Save tokens**: Summary-only views and pagination
- **Streamline auth**: Header mounting eliminates repetitive header passing
- **Faster testing**: Direct API calls from within the agent context

### For API Teams
- **Better documentation consumption**: AI agents can explore your API naturally
- **Automated testing**: Agents can test endpoints programmatically
- **Multi-API workflows**: Work with multiple specs simultaneously

### For Researchers/Students
- **Learn by exploring**: Fuzzy search makes discovering endpoints intuitive
- **Experiment safely**: Test API calls with built-in error handling
- **Open source**: Study the code, contribute, customize

---

## 🔗 Important Links

- **GitHub**: https://github.com/mikegaruccio/openapi-navigator
- **PyPI**: https://pypi.org/project/openapi-navigator/
- **Documentation**: See README.md in repository
- **Issues**: https://github.com/mikegaruccio/openapi-navigator/issues
- **CI Status**: https://github.com/mikegaruccio/openapi-navigator/actions
- **License**: MIT

---

## 📞 Contact Information

**Author**: Mike Garuccio
**Email**: mike.garuccio@expedient.com
**GitHub**: @mikegaruccio

---

## ✅ Submission Checklist

Before submitting to registries:

- [ ] Verify all links work
- [ ] Ensure README.md has PyPI marker: `<!-- mcp-name: openapi-navigator -->`
- [ ] Confirm latest version (0.5.0) is on PyPI
- [ ] Test installation: `uvx openapi-navigator`
- [ ] Review submission description for typos
- [ ] Prepare contact email for registry notifications
- [ ] Have GitHub repo URL ready
- [ ] Decide on free vs paid submission (MCPServers.org)
- [ ] Review category selection (development/api-tools/productivity)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Generated for**: OpenAPI Navigator v0.5.0

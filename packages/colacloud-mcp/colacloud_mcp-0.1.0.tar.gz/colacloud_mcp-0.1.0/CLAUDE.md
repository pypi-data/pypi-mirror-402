# colacloud-mcp

MCP server that exposes COLA Cloud API as tools for AI assistants. See root `../CLAUDE.md` for project-wide context.

## Build/Test Commands

```bash
uv sync --dev              # Install dependencies
uv run colacloud-mcp       # Run server (requires COLA_API_KEY)
uv run pytest              # Run tests
uv run pytest -v           # Run tests with verbose output
uv run ruff check .        # Lint
uv run ruff format .       # Format
```

## Architecture

- `src/colacloud_mcp/server.py` - FastMCP server with tool definitions
- `src/colacloud_mcp/client.py` - HTTP client wrapping COLA Cloud REST API

The MCP server calls the existing REST API (`app.colacloud.us/api/v1`) rather than accessing the database directly. This reuses existing rate limiting, authentication, and serialization.

## Tools

| Tool | API Endpoint |
|------|--------------|
| `search_colas` | `GET /colas` |
| `get_cola` | `GET /colas/<ttb_id>` |
| `search_permittees` | `GET /permittees` |
| `get_permittee` | `GET /permittees/<permit_number>` |
| `lookup_barcode` | `GET /barcode/<value>` |
| `get_api_usage` | `GET /usage` |

## Environment Variables

- `COLA_API_KEY` (required) - API key from app.colacloud.us
- `COLA_API_URL` (optional) - Override API base URL (default: `https://app.colacloud.us/api/v1`)

## Publishing

```bash
uv build                   # Build wheel and sdist
uv publish                 # Publish to PyPI (needs credentials)
```

## Testing Locally with Claude Desktop

1. Build and install locally:
   ```bash
   uv build
   pip install dist/colacloud_mcp-*.whl
   ```

2. Configure Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "colacloud": {
         "command": "colacloud-mcp",
         "env": { "COLA_API_KEY": "your-key" }
       }
     }
   }
   ```

3. Restart Claude Desktop

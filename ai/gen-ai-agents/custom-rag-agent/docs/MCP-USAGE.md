# MCP (Model Context Protocol) Usage

MCP allows LLMs to access external tools and data sources. This project includes MCP servers that expose semantic search capabilities for your vector database.

## Quick Start

### 1. Start the MCP Server
```bash
source .venv/bin/activate
python mcp_servers/mcp_semantic_search.py
```
Server starts on `http://localhost:9000`

### 2. Start the UI (in a new terminal)
```bash
streamlit run ui/ui_mcp_agent.py
```

### 3. Use the UI
1. Open browser to the Streamlit URL (usually `http://localhost:8501`)
2. Click **"🔌 Connect / Reload tools"** in the sidebar
3. Ask a question - the LLM will automatically use MCP tools to search your database

## Available MCP Servers

- **`mcp_semantic_search.py`** - Main server with HTTP transport
- **`mcp_semantic_search_stdio.py`** - For Claude Desktop (stdio transport)
- **`mcp_semantic_search_with_iam.py`** - With OCI IAM JWT authentication
- **`minimal_mcp_server.py`** - Minimal example for learning

## Available Tools

1. **`semantic_search`** - Search for relevant documents
   - Parameters: `query` (required), `top_k` (default: 5), `collection_name` (optional)

2. **`list_collections`** - List all available collections

3. **`list_documents_in_collection`** - List documents in a specific collection
   - Parameters: `collection_name` (optional)

## Configuration

In `config.py`:
- `PORT = 9000` - MCP server port
- `HOST = "0.0.0.0"` - Listen on all interfaces
- `TRANSPORT = "streamable-http"` - Use `"stdio"` for Claude Desktop
- `ENABLE_JWT_TOKEN = False` - Set to `True` for JWT authentication

For JWT authentication, use `mcp_semantic_search_with_iam.py` and configure:
- `IAM_BASE_URL`, `ISSUER`, `AUDIENCE` in `config.py`

## Testing

### Using Python
```python
import asyncio
from fastmcp import Client

async def test():
    client = Client("http://localhost:9000/mcp/")
    async with client:
        result = await client.call_tool(
            "semantic_search",
            {"query": "Oracle 23AI", "top_k": 5}
        )
        print(result)

asyncio.run(test())
```

### Using cURL
```bash
curl -X POST http://localhost:9000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool
```

## Common Issues

**404 in Browser**: Normal! MCP servers are APIs, not web pages. Use the UI or test scripts.

**Connection Refused**: Ensure the server is running and check the port in `config.py`.

**Import Errors**: Activate virtual environment and verify dependencies are installed.

**Database Errors**: Verify database connection settings in `config.py`.

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

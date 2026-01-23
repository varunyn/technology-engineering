# MCP (Model Context Protocol) Usage Guide

This guide explains how to test and use the MCP servers in this project.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows LLMs to access external tools and data sources. In this project, MCP servers expose semantic search capabilities as tools that can be called by LLM agents.

## Available MCP Servers

1. **`mcp_semantic_search.py`** - Main semantic search MCP server with HTTP transport
2. **`mcp_semantic_search_stdio.py`** - Semantic search with stdio transport (for Claude Desktop)
3. **`mcp_semantic_search_with_iam.py`** - Semantic search with OCI IAM JWT authentication
4. **`minimal_mcp_server.py`** - Minimal example server for learning

## Prerequisites

1. Ensure your database is configured and accessible
2. Make sure `config.py` has the correct settings:
   - `PORT = 9000` (default MCP server port)
   - `HOST = "0.0.0.0"` (listen on all interfaces)
   - `TRANSPORT = "streamable-http"` (or "stdio" for Claude Desktop)
   - `ENABLE_JWT_TOKEN = False` (set to `True` if using JWT auth)

## Method 1: Using the Streamlit UI (Easiest)

The easiest way to test MCP is through the provided Streamlit UI:

```bash
streamlit run ui/ui_mcp_agent.py
```

**Steps:**
1. Open the UI in your browser (usually `http://localhost:8501`)
2. In the sidebar, configure:
   - **MCP URL**: `http://localhost:9000/mcp/` (default)
   - **Model**: Select your LLM model
   - **Timeout**: Set connection timeout
3. Click **"🔌 Connect / Reload tools"** to connect to the MCP server
4. Once connected, you can ask questions and the LLM will use MCP tools automatically

**Note:** Make sure the MCP server is running first (see Method 2).

## Method 2: Running the MCP Server

### Start the Semantic Search MCP Server

```bash
# Activate your virtual environment
source .venv/bin/activate

# Run the main MCP server
python mcp_servers/mcp_semantic_search.py
```

The server will start on `http://localhost:9000` (or the port specified in `config.py`).

### Available Tools

Once the server is running, it exposes these tools:

1. **`semantic_search`** - Search for relevant documents
   - Parameters:
     - `query` (str): The search query
     - `top_k` (int): Number of results (default: 5)
     - `collection_name` (str, optional): Database collection/table name. If not provided, uses default from config.

2. **`list_collections`** - List all available collections

3. **`list_documents_in_collection`** - List documents/sources in a specific collection
   - Parameters:
     - `collection_name` (str, optional): Name of the collection. If not provided, uses default from config.
   - Returns: List of tuples with (document_source, chunk_count)

## Method 3: Testing with Python Script

You can test the MCP server programmatically:

```python
import asyncio
from fastmcp import Client

async def test_mcp():
    endpoint = "http://localhost:9000/mcp/"
    client = Client(endpoint)
    
    async with client:
        # Call semantic_search tool
        results = await client.call_tool(
            "semantic_search",
            {
                "query": "What is Oracle AI Vector Search?",
                "top_k": 5,
                # collection_name is optional - uses default from config
            }
        )
        print(results)

asyncio.run(test_mcp())
```

## Method 4: Using the Test Script

A test script is provided in `tests/test_mcp_semantic_search.py`:

```bash
# First, make sure the MCP server is running
python mcp_servers/mcp_semantic_search.py

# In another terminal, run the test
python tests/test_mcp_semantic_search.py
```

**Note:** You may need to update the test script imports to work with the new structure.

## Method 5: Integration with LLM Agents

The MCP server can be integrated with LLM agents using the `AgentWithMCP` class:

```python
from scripts.llm_with_mcp import AgentWithMCP, default_jwt_supplier

# Create an agent with MCP support
agent = await AgentWithMCP.create(
    mcp_url="http://localhost:9000/mcp/",
    jwt_supplier=default_jwt_supplier,  # For JWT auth (if enabled)
    timeout=60,
    model_id="cohere.command-a-03-2025"
)

# Use the agent
answer = await agent.answer("What is Oracle 23AI?", [])
print(answer)
```

## Configuration Options

### Transport Types

- **`streamable-http`** (default): HTTP-based transport, good for web applications
- **`stdio`**: Standard input/output, used for Claude Desktop integration

### JWT Authentication

If you want to enable JWT authentication:

1. Set `ENABLE_JWT_TOKEN = True` in `config.py`
2. Configure JWT settings:
   - `IAM_BASE_URL`: OCI IAM base URL
   - `ISSUER`: JWT issuer
   - `AUDIENCE`: JWT audience
3. Use `mcp_semantic_search_with_iam.py` instead

### Port Configuration

Change the port in `config.py`:
```python
PORT = 9000  # Change to your preferred port
```

## Troubleshooting

### Server won't start
- Check if the port is already in use: `lsof -i :9000`
- Verify database connection settings in `config_private.py`
- Check that all dependencies are installed

### Connection refused
- Ensure the MCP server is running
- Verify the URL matches the server configuration
- Check firewall settings

### JWT authentication errors
- Verify JWT settings in `config.py` and `config_private.py`
- Ensure OCI IAM is properly configured
- Check that tokens are being generated correctly

### Import errors
- Make sure you're running from the project root
- Activate the virtual environment
- Verify all dependencies are installed: `uv pip install -r requirements.txt`

## Example Workflow

1. **Start the MCP server:**
   ```bash
   python mcp_servers/mcp_semantic_search.py
   ```

2. **In another terminal, start the UI:**
   ```bash
   streamlit run ui/ui_mcp_agent.py
   ```

3. **In the UI:**
   - Connect to the MCP server
   - Ask a question like: "What documents mention Oracle 23AI?"
   - The LLM will automatically use the `semantic_search` tool to find relevant documents

## Next Steps

- Explore the different MCP server implementations
- Customize the tools in `mcp_semantic_search.py`
- Integrate MCP with your own LLM applications
- Add new tools to the MCP server

For more information, see:
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

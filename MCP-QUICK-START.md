# MCP Quick Start Guide

## Quick Test (3 Steps)

### Step 1: Start the MCP Server
```bash
source .venv/bin/activate
python mcp_servers/mcp_semantic_search.py
```
Server will start on `http://localhost:9000`

### Step 2: Start the UI (in a new terminal)
```bash
source .venv/bin/activate
streamlit run ui/ui_mcp_agent.py
```

### Step 3: Use the UI
1. Open browser to the Streamlit URL (usually http://localhost:8501)
2. Click "🔌 Connect / Reload tools" in the sidebar
3. Ask a question like: "What is Oracle 23AI?"
4. The LLM will use MCP tools to search your database!

## Alternative: Test with Python Script

```python
import asyncio
from fastmcp import Client

async def test():
    client = Client("http://localhost:9000/mcp/")
    async with client:
            result = await client.call_tool(
                "semantic_search",
                {"query": "Oracle 23AI", "top_k": 5}
                # collection_name is optional - uses default from config if not provided
            )
        print(result)

asyncio.run(test())
```

For detailed documentation, see `docs/MCP-USAGE.md`

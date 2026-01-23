# Testing the MCP Server

## Understanding the 404 Error

**The 404 errors you see are normal!** MCP servers are **API endpoints**, not web pages. They don't serve HTML content, so accessing them in a browser will show 404 errors.

The MCP server is working correctly if you see:
```
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

## How to Test the MCP Server

### Method 1: Use the Streamlit UI (Recommended)

The easiest way to test is through the provided UI:

```bash
# Terminal 1: Start MCP server
python mcp_servers/mcp_semantic_search.py

# Terminal 2: Start UI
streamlit run ui/ui_mcp_agent.py
```

Then in the browser:
1. Go to the Streamlit URL (usually http://localhost:8501)
2. Click "🔌 Connect / Reload tools"
3. Ask a question - the LLM will use MCP tools automatically

### Method 2: Test with Python Script

Create a test script:

```python
import asyncio
from fastmcp import Client

async def test_mcp():
    endpoint = "http://localhost:9000/mcp/"
    client = Client(endpoint)
    
    async with client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])
        
        # Call semantic_search
        result = await client.call_tool(
            "semantic_search",
            {
                "query": "What is Oracle 23AI?",
                "top_k": 5,
                "collection_name": "BOOKS"
            }
        )
        print("\nSearch results:")
        print(result)

asyncio.run(test_mcp())
```

### Method 3: Test with cURL (Command Line)

Test the MCP server directly:

```bash
# List available tools
curl -X POST http://localhost:9000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Call semantic_search tool
curl -X POST http://localhost:9000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "semantic_search",
      "arguments": {
        "query": "Oracle 23AI",
        "top_k": 5,
        "collection_name": "BOOKS"
      }
    }
  }'
```

### Method 4: Use the Provided Test Script

```bash
# Make sure MCP server is running first
python mcp_servers/mcp_semantic_search.py

# In another terminal
python tests/test_mcp_semantic_search.py
```

## Expected Behavior

### ✅ Server is Working If:
- You see `INFO: Uvicorn running on http://0.0.0.0:9000`
- No error messages in the terminal
- The UI can connect successfully
- Test scripts can call tools

### ❌ Server is NOT Working If:
- You see import errors
- Connection refused errors
- Database connection errors
- Authentication errors (if JWT is enabled)

## Common Issues

### Issue: 404 in Browser
**Solution:** This is normal! MCP servers are APIs, not web pages. Use the UI or test scripts instead.

### Issue: Connection Refused
**Solution:** 
- Make sure the server is running
- Check the port in `config.py` matches (default: 9000)
- Verify no firewall is blocking the port

### Issue: Import Errors
**Solution:**
- Make sure you're in the virtual environment
- Verify all dependencies are installed: `uv pip install -r requirements.txt`
- Check that `mcp_servers/` directory exists (not `mcp/`)

### Issue: Database Errors
**Solution:**
- Verify database connection in `config_private.py`
- Ensure the database is accessible
- Check that collections/tables exist

## Quick Verification

Run this to verify the server is responding:

```bash
curl -X POST http://localhost:9000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m json.tool
```

You should see a JSON response with available tools like `semantic_search`, `list_collections`, etc.

## Next Steps

Once the server is running:
1. Use the Streamlit UI for interactive testing
2. Integrate with your LLM applications
3. Add custom tools to the MCP server
4. Configure JWT authentication if needed

For more details, see `MCP-USAGE.md`.

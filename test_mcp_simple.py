#!/usr/bin/env python3
"""Simple MCP server test script"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastmcp import Client

async def test():
    """Test MCP server connection and tools"""
    endpoint = "http://localhost:9000/mcp/"
    print(f"Connecting to MCP server at {endpoint}...")
    
    try:
        client = Client(endpoint)
        async with client:
            # List available tools
            print("\n📋 Listing available tools...")
            tools = await client.list_tools()
            print(f"✓ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test semantic_search
            print("\n🔍 Testing semantic_search...")
            # Use default collection from config
            import config
            collection_name = config.COLLECTION_LIST[0] if config.COLLECTION_LIST else "DOCUMENT_CHUNKS_VS"
            
            result = await client.call_tool(
                "semantic_search",
                {
                    "query": "Oracle 23AI",
                    "top_k": 3,
                    "collection_name": collection_name
                }
            )
            print("✓ Search completed!")
            print(f"Result type: {type(result)}")
            if result:
                print(f"Result: {result[0].text[:200]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing MCP Server")
    print("=" * 50)
    asyncio.run(test())

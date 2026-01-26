"""
Test Semantic Search MCP Server

Usage:
    # First, start the MCP server in another terminal:
    python mcp_servers/mcp_semantic_search.py
    
    # Then run this test:
    python tests/test_mcp_semantic_search.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
from fastmcp import Client
from src.rag_agent.infrastructure.jwt_utils import create_jwt_token
import config

ENDPOINT = f"http://localhost:{config.PORT}/mcp/"


async def main():
    """
    Main function to demonstrate the semantic search tool.
    """
    # create the JWT token
    # can pass a user here
    if config.ENABLE_JWT_TOKEN:
        token = create_jwt_token()
        client = Client(ENDPOINT, auth=token)
    else:
        token = ""
        client = Client(ENDPOINT)

    async with client:
        print("")
        print("\nCalling semantic_search tool...")
        print("")

        query = "What is Oracle AI Vector Search?"

        # Use default collection from config or specify one
        collection_name = config.COLLECTION_LIST[0] if config.COLLECTION_LIST else "DOCUMENT_CHUNKS_VS"
        
        results = await client.call_tool(
            "semantic_search",
            {
                "query": query,
                "top_k": 5,
                "collection_name": collection_name,
            },
        )

        relevant_docs = json.loads(results[0].text)["relevant_docs"]

        print("--- Query: ", query)
        print("Search Results:")
        print("")
        for doc in relevant_docs:
            print(doc["page_content"])
            print("Metadata:", doc["metadata"])
            print("")


asyncio.run(main())

"""
Semantic Search exposed as an MCP tool
This version uses stdio (local) as transport

Author: L. Saetta
License: MIT

This one requires, if enabled, that a token is generated using the library PyJWT.
See the associated client
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP

from src.rag_agent.utils.utils import get_console_logger
from src.rag_agent.infrastructure.oci_models import get_embedding_model, get_oracle_vs
from src.rag_agent.infrastructure.db_utils import get_connection, list_collections, list_books_in_collection
import config as app_config

logger = get_console_logger()

# local, stdio, to test Claude integration
# TRANSPORT is set to "stdio" for this version

mcp = FastMCP("Demo Semantic Search as MCP server")


#
# Helper functions
#


#
# MCP tools definition
#
@mcp.tool
def semantic_search(
    query: Annotated[
        str, Field(description="The search query to find relevant documents.")
    ],
    top_k: Annotated[int, Field(description="TOP_K parameter for search")] = 5,
    collection_name: Annotated[
        str, Field(description="The name of the collection (table) to search in")
    ] = None,
) -> dict:
    """
    Perform a semantic search based on the provided query.
    Args:
        query (str): The search query.
        top_k (int): The number of top results to return.
        collection_name (str): The name of the collection (table) to search in.
                              If not provided, uses the default collection from config.
    Returns:
        dict: a dictionary containing the relevant documents.
    """
    # Use default collection if not provided
    if collection_name is None:
        collection_name = app_config.COLLECTION_LIST[0] if app_config.COLLECTION_LIST else "DOCUMENT_CHUNKS_VS"

    try:
        # must be the same embedding model used during load in the Vector Store
        embed_model = get_embedding_model(app_config.EMBED_MODEL_TYPE)

        # get a connection to the DB and init VS
        with get_connection() as conn:
            v_store = get_oracle_vs(
                conn=conn,
                collection_name=collection_name,
                embed_model=embed_model,
            )
            relevant_docs = v_store.similarity_search(query=query, k=top_k)

            # (L.S.) we could additionally plug a reranker here

            if app_config.DEBUG:
                logger.info("Result from the similarity search:")
                logger.info(relevant_docs)

    except Exception as e:
        logger.error("Error in MCP similarity search: %s", e)
        error = str(e)
        return {"error": error}

    result = {"relevant_docs": relevant_docs}

    return result


@mcp.tool
def get_collections() -> list:
    """
    Get the list of collections (DB tables) available in the Oracle Vector Store.
    Returns:
        list: A list of collection names.
    """

    return list_collections()


@mcp.tool
def list_documents_in_collection(
    collection_name: Annotated[
        str, Field(description="The name of the collection (table) to list documents from")
    ] = None,
) -> list:
    """
    Get the list of documents/sources in a specific collection.
    This returns unique document sources from the collection's metadata along with chunk counts.
    
    Args:
        collection_name (str): The name of the collection (table) to list from.
                              If not provided, uses the default collection from config.
    Returns:
        list: A list of tuples containing (document_source, chunk_count) for each unique document.
    """
    # Use default collection if not provided
    if collection_name is None:
        collection_name = app_config.COLLECTION_LIST[0] if app_config.COLLECTION_LIST else "DOCUMENT_CHUNKS_VS"

    try:
        documents = list_books_in_collection(collection_name)
        return documents
    except Exception as e:
        logger.error("Error getting documents in collection: %s", e)
        return []


if __name__ == "__main__":
    mcp.run(
        transport="stdio",
    )

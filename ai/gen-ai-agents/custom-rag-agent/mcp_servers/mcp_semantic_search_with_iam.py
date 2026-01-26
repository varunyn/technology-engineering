"""
Semantic Search exposed as an MCP tool
with added security with OCI IAM and JWT tokens

Author: L. Saetta
License: MIT
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP

# to verify the JWT token
# Updated to use JWTVerifier (BearerAuthProvider deprecated in v2.14.0)
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_http_headers

from src.rag_agent.utils.utils import get_console_logger
from src.rag_agent.infrastructure.oci_models import get_embedding_model, get_oracle_vs
from src.rag_agent.infrastructure.db_utils import get_connection, list_collections, list_books_in_collection
import config as app_config

logger = get_console_logger()

AUTH = None

if app_config.ENABLE_JWT_TOKEN:
    # check that a valid JWT token is provided
    # see docs here: https://gofastmcp.com/servers/auth/authentication
    # Using JWTVerifier (replaces deprecated BearerAuthProvider in v2.14.0+)
    AUTH = JWTVerifier(
        # this is the url to get the public key from IAM
        jwks_uri=f"{app_config.IAM_BASE_URL}/admin/v1/SigningCert/jwk",
        issuer=app_config.ISSUER,
        audience=app_config.AUDIENCE,
    )

# create the app
# cool, the OAUTH 2.1 provider is pluggable
mcp = FastMCP("Demo Semantic Search as MCP server", auth=AUTH)


#
# Helper functions
#
def log_headers():
    """
    if DEBUG log the headers in the HTTP request
    """
    if app_config.DEBUG:
        headers = get_http_headers(include_all=True)
        logger.info("Headers: %s", headers)


#
# MCP tools definition
#
@mcp.tool
def get_collections() -> list:
    """
    Get the list of collections (DB tables) available in the Oracle Vector Store.
    Returns:
        list: A list of collection names.
    """
    # check that a valid JWT is provided
    if app_config.ENABLE_JWT_TOKEN:
        log_headers()

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
    # check that a valid JWT is provided
    if app_config.ENABLE_JWT_TOKEN:
        log_headers()

    # Use default collection if not provided
    if collection_name is None:
        collection_name = app_config.COLLECTION_LIST[0] if app_config.COLLECTION_LIST else "DOCUMENT_CHUNKS_VS"

    try:
        documents = list_books_in_collection(collection_name)
        return documents
    except Exception as e:
        logger.error("Error getting documents in collection: %s", e)
        return []


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
        top_k (int): The number of top results to return. Must be at least 5.
        collection_name (str): The name of the collection (table) to search in.
                              If not provided, uses the default collection from config.
    Returns:
        dict: a dictionary containing the relevant documents.
    """
    # here only log
    if app_config.ENABLE_JWT_TOKEN:
        log_headers()
        # no verification here, delegated to JWTVerifier

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

            if app_config.DEBUG:
                logger.info("Result from the similarity search:")
                logger.info(relevant_docs)

    except Exception as e:
        logger.error("Error in MCP similarity search: %s", e)
        error = str(e)
        return {"error": error}

    result = {"relevant_docs": relevant_docs}

    return result


#
# Run the MCP server
#

if __name__ == "__main__":
    if app_config.DEBUG:
        LOG_LEVEL = "DEBUG"
    else:
        LOG_LEVEL = "INFO"

    mcp.run(
        transport=app_config.TRANSPORT,
        # Bind to all interfaces
        host=app_config.HOST,
        port=app_config.PORT,
        log_level=LOG_LEVEL,
    )

"""
File name: reranker.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    This module implements filtering and reranking documents
    returned by Similarity Search, using a LLM

Usage:
    Import this module into other scripts to use its functions.
    Example:
        import config

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

# Import traceback for better error logging
import traceback
from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

# integration with APM
from py_zipkin.zipkin import zipkin_span

from .agent_state import State
from .prompts import (
    RERANKER_TEMPLATE,
)
from .infrastructure.oci_models import get_llm
from .utils.utils import get_console_logger, extract_json_from_text
import config as app_config

logger = get_console_logger()


class Reranker(Runnable):
    """
    Implements a reranker using a LLM
    """

    def __init__(self):
        """
        Init
        """

    def generate_refs(self, docs: list):
        """
        Returns a list of reference dictionaries used in the reranker.
        """
        citations = []
        for doc in docs:
            metadata = doc.get("metadata", {})
            # Handle different metadata structures
            source = metadata.get("source") or metadata.get("source_url") or metadata.get("file_path") or "Unknown"
            page = metadata.get("page_label") or metadata.get("page") or metadata.get("chunk_offset") or ""
            citations.append({"source": source, "page": page})
        return citations

    @staticmethod
    def get_reranked_docs(llm, query, retriever_docs):
        """
        Rerank documents using LLM based on user request.

        query: the search query (can be reformulated)
        retriever_docs: list of dicts with page_content and metadata (from docs_serializable)
        """
        # Prepare chunk texts - handle both dict format and Document format
        chunks = []
        for doc in retriever_docs:
            if isinstance(doc, dict):
                chunks.append(doc.get("page_content", ""))
            else:
                # LangChain Document object
                chunks.append(doc.page_content if hasattr(doc, 'page_content') else str(doc))

        _prompt = PromptTemplate(
            input_variables=["query", "chunks"],
            template=RERANKER_TEMPLATE,
        ).format(query=query, chunks=chunks)

        messages = [HumanMessage(content=_prompt)]

        response = llm.invoke(messages)
        # Handle different response types
        if hasattr(response, 'content'):
            reranker_output = response.content
        elif isinstance(response, str):
            reranker_output = response
        else:
            reranker_output = str(response)

        # Extract ranking order
        json_dict = extract_json_from_text(reranker_output)

        if app_config.DEBUG:
            logger.info(json_dict.get("ranked_chunks", "No ranked chunks found."))

        # Get indexes and sort documents
        # added < TOP_K (hallucinations ?)
        indexes = [
            chunk["index"]
            for chunk in json_dict.get("ranked_chunks", [])
            if chunk["index"] < app_config.TOP_K
        ]

        return [retriever_docs[i] for i in indexes]

    @zipkin_span(service_name=app_config.AGENT_NAME, span_name="reranking")
    def invoke(self, input: State, config=None, **kwargs):
        """
        Implements reranking logic.

        input: The agent state.
        """
        # Rename parameter to avoid shadowing the config module
        run_config = config
        enable_reranker = run_config["configurable"]["enable_reranker"]

        user_request = input.get("standalone_question", "")
        retriever_docs = input.get("retriever_docs", [])
        error = None

        if app_config.DEBUG:
            logger.info("Reranker input state: %s", input)

        try:
            if retriever_docs:
                # there is something to rerank!
                if enable_reranker:
                    # do reranking
                    llm = get_llm(temperature=0.0)

                    reranked_docs = self.get_reranked_docs(
                        llm, user_request, retriever_docs
                    )

                else:
                    reranked_docs = retriever_docs
            else:
                reranked_docs = []

        except Exception as e:
            logger.error("Error in reranker: %s", e)
            # Log the full stack trace for debugging
            logger.debug(traceback.format_exc())
            error = str(e)
            # Fallback to original documents
            reranked_docs = retriever_docs

        # Get reference citations
        citations = self.generate_refs(reranked_docs)

        return {"reranker_docs": reranked_docs, "citations": citations, "error": error}

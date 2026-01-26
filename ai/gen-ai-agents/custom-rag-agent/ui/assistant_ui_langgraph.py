"""
File name: assistant_ui.py
Author: Luigi Saetta
Date created: 2024-12-04
Date last modified: 2025-07-01
Python Version: 3.11

Description:
    This module provides the UI for the RAG demo

Usage:
    streamlit run assistant_ui_langgraph.py

License:
    This code is released under the MIT License.

Notes:
    This is part of a  demo for a RAG solution implemented
    using LangGraph

Warnings:
    This module is in development, may change in future versions.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uuid
from typing import List, Union
import time
import streamlit as st

from langchain_core.messages import HumanMessage, AIMessage

# for APM integration
from py_zipkin.zipkin import zipkin_span
from py_zipkin import Encoding

from src.rag_agent import State, create_workflow
from src.rag_agent.utils.rag_feedback import RagFeedback
from src.rag_agent.infrastructure.transport import http_transport
from src.rag_agent.utils.utils import get_console_logger

# changed to better manage ENABLE_TRACING (can be enabled from UI)
import config


def display_citations(citations: List[dict], reranker_docs: List[dict]):
    """
    Display citations with clickable file links and chunk content preview.
    
    Args:
        citations: List of citation dicts with 'source' and 'page' keys
        reranker_docs: List of document dicts with 'page_content' and 'metadata'
    """
    if not citations:
        st.write("No references found.")
        return
    
    # Limit citations shown to prevent sidebar overflow
    if "max_citations_display" not in st.session_state:
        st.session_state.max_citations_display = 10
    
    max_citations_to_show = st.session_state.max_citations_display
    
    # Show toggle buttons if there are more citations
    if len(citations) > 10:
        col1, col2 = st.columns([2, 1])
        with col1:
            if max_citations_to_show < len(citations):
                st.caption(f"Showing {max_citations_to_show} of {len(citations)} references")
            else:
                st.caption(f"Showing all {len(citations)} references")
        with col2:
            if max_citations_to_show < len(citations):
                if st.button("Show All", key="show_all_citations", use_container_width=True):
                    st.session_state.max_citations_display = len(citations)
                    st.rerun()
            else:
                if st.button("Show Less", key="show_less_citations", use_container_width=True):
                    st.session_state.max_citations_display = 10
                    st.rerun()
    
    # Citations are generated in the same order as reranker_docs
    # So citation[i] corresponds to reranker_docs[i]
    for i, citation in enumerate(citations[:max_citations_to_show]):
        source = citation.get("source", "Unknown")
        page = citation.get("page", "")
        
        # Get the document content for this specific citation by index
        doc = reranker_docs[i] if i < len(reranker_docs) else None
        chunk_content = doc.get("page_content", "") if doc else ""
        
        # Extract filename from source path
        filename = Path(source).name if source != "Unknown" else "Unknown"
        
        # Create expandable citation with file link
        with st.expander(f"📄 {filename}", expanded=False):
            # Display source path
            if source != "Unknown":
                st.markdown(f"**File:** `{source}`")
            else:
                st.markdown(f"**Source:** {source}")
            
            # Display page/chunk offset if available
            if page:
                st.markdown(f"**Location:** Chunk offset {page}")
            
            # Show chunk content preview
            if chunk_content:
                st.markdown("**Relevant Content:**")
                # Limit preview to first 500 characters
                preview = chunk_content[:500] + "..." if len(chunk_content) > 500 else chunk_content
                st.text_area(
                    "Content preview",
                    value=preview,
                    height=150,
                    key=f"citation_preview_{i}",
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            # Try to open file if it exists
            if source != "Unknown":
                file_path = project_root / source
                if file_path.exists():
                    # Determine file type
                    file_ext = file_path.suffix.lower()
                    
                    if file_ext in ['.txt', '.md', '.markdown']:
                        # For text files, show full content in expander
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            # Try to highlight the chunk if we have chunk_offset
                            if page and chunk_content:
                                st.markdown("**Full File Content:**")
                                # Find the chunk in the file content
                                chunk_start = file_content.find(chunk_content[:100])  # Find first 100 chars
                                if chunk_start != -1:
                                    # Show context around the chunk
                                    context_start = max(0, chunk_start - 200)
                                    context_end = min(len(file_content), chunk_start + len(chunk_content) + 200)
                                    highlighted_content = file_content[context_start:context_end]
                                    st.code(highlighted_content, language='text')
                                else:
                                    st.code(file_content, language='text')
                            else:
                                st.markdown("**Full File Content:**")
                                st.code(file_content, language='text')
                        except Exception as e:
                            st.warning(f"Could not read file: {e}")
                    
                    elif file_ext == '.pdf':
                        # For PDFs, provide download link
                        try:
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=f.read(),
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=f"download_{i}"
                                )
                        except Exception as e:
                            st.warning(f"Could not open PDF: {e}")
                    
                    else:
                        # For other file types, provide download link
                        try:
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                    label=f"📥 Download {file_ext.upper()[1:]}",
                                    data=f.read(),
                                    file_name=filename,
                                    key=f"download_{i}"
                                )
                        except Exception as e:
                            st.warning(f"Could not open file: {e}")
                else:
                    st.warning(f"File not found: {source}")

# Constant

# name for the roles
USER = "user"
ASSISTANT = "assistant"

logger = get_console_logger()


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "workflow" not in st.session_state:
    st.session_state.workflow = create_workflow()
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "model_id" not in st.session_state:
    st.session_state.model_id = "meta.llama3.3-70B"
if "main_language" not in st.session_state:
    st.session_state.main_language = "en"
if "enable_reranker" not in st.session_state:
    st.session_state.enable_reranker = True
if "collection_name" not in st.session_state:
    st.session_state.collection_name = config.COLLECTION_LIST[0]
if "get_feedback" not in st.session_state:
    st.session_state.get_feedback = False
if "enable_tracing" not in st.session_state:
    st.session_state.enable_tracing = False


#
# supporting functions
#
def display_msg_on_rerun(chat_hist: List[Union[HumanMessage, AIMessage]]) -> None:
    """Display all messages on rerun."""
    for msg in chat_hist:
        role = USER if isinstance(msg, HumanMessage) else ASSISTANT
        with st.chat_message(role):
            st.markdown(msg.content)


# when push the button reset the chat_history
def reset_conversation():
    """Reset the chat history."""
    st.session_state.chat_history = []

    # change thread_id
    st.session_state.thread_id = str(uuid.uuid4())


def add_to_chat_history(msg):
    """
    add the msg to chat history
    """
    st.session_state.chat_history.append(msg)


def get_chat_history():
    """return the chat history from the session"""
    return (
        st.session_state.chat_history[-config.MAX_MSGS_IN_HISTORY :]
        if config.MAX_MSGS_IN_HISTORY > 0
        else st.session_state.chat_history
    )


def register_feedback():
    """
    Register the feedback.
    """
    # number of stars, start at 0
    n_stars = st.session_state.feedback + 1
    logger.info("Feedback: %d %s", n_stars, "stars")
    logger.info("")

    # register the feedback in DB
    rag_feedback = RagFeedback()

    rag_feedback.insert_feedback(
        question=st.session_state.chat_history[-2].content,
        answer=st.session_state.chat_history[-1].content,
        feedback=n_stars,
    )

    st.session_state.get_feedback = False


#
# Main
#
st.title("OCI Custom RAG Agent")

# Reset button
if st.sidebar.button("Clear Chat History"):
    reset_conversation()


st.sidebar.header("Options")

st.sidebar.text_input(label="Region", value=config.REGION, disabled=True)

# the collection used for semantic search
st.session_state.collection_name = st.sidebar.selectbox(
    "Collection name",
    config.COLLECTION_LIST,
)

st.session_state.main_language = st.sidebar.selectbox(
    "Select the language for the answer",
    config.LANGUAGE_LIST,
)
st.session_state.model_id = st.sidebar.selectbox(
    "Select the Chat Model",
    config.MODEL_LIST,
)

st.sidebar.text_input(label="Embed Model", value=config.EMBED_MODEL_ID, disabled=True)

st.session_state.enable_reranker = st.sidebar.checkbox(
    "Enable Reranker", value=st.session_state.enable_reranker
)
st.session_state.enable_tracing = st.sidebar.checkbox(
    "Enable tracing", value=st.session_state.enable_tracing
)


#
# Here the code where react to user input
#

# Display chat messages from history on app rerun
display_msg_on_rerun(get_chat_history())

if question := st.chat_input("Hello, how can I help you?"):
    # Display user message in chat message container
    st.chat_message(USER).markdown(question)

    try:
        with st.spinner("Calling AI..."):
            time_start = time.time()

            # get the chat history to give as input to LLM
            _chat_history = get_chat_history()

            # modified to be more responsive, show result asap
            try:
                input_state = State(
                    user_request=question,
                    chat_history=_chat_history,
                    error=None,
                )

                # collect the results of all steps
                results = []
                ERROR = None

                # integration with tracing, start the trace
                with zipkin_span(
                    service_name=config.AGENT_NAME,
                    span_name="stream",
                    transport_handler=http_transport,
                    encoding=Encoding.V2_JSON,
                    sample_rate=100,
                ) as span:
                    # set the agent config
                    agent_config = {
                        "configurable": {
                            "model_id": st.session_state.model_id,
                            "embed_model_type": config.EMBED_MODEL_TYPE,
                            "enable_reranker": st.session_state.enable_reranker,
                            "enable_tracing": st.session_state.enable_tracing,
                            "main_language": st.session_state.main_language,
                            "collection_name": st.session_state.collection_name,
                            "thread_id": st.session_state.thread_id,
                        }
                    }

                    if config.DEBUG:
                        logger.info("Agent config: %s", agent_config)

                    # loop to manage streaming
                    answer_generator = None
                    for event in st.session_state.workflow.stream(
                        input_state,
                        config=agent_config,
                    ):
                        for key, value in event.items():
                            MSG = f"Completed: {key}!"
                            logger.info(MSG)
                            st.toast(MSG)

                            # to see if there has been an error
                            ERROR = value.get("error")

                            # update UI asap
                            if key == "QueryRewrite":
                                with st.sidebar:
                                    st.header("Standalone question:")
                                    st.write(value["standalone_question"])
                            if key == "Rerank":
                                with st.sidebar:
                                    st.header("References:")
                                    display_citations(value.get("citations", []), value.get("reranker_docs", []))
                            
                            # Extract generator immediately to avoid serialization issues
                            if key == "Answer" and "final_answer" in value:
                                answer_generator = value["final_answer"]
                                # Don't store generator in results to avoid serialization
                                value_without_generator = {k: v for k, v in value.items() if k != "final_answer"}
                                results.append(value_without_generator)
                            else:
                                results.append(value)

                # process final result from agent
                FULL_RESPONSE = ""  # Initialize to avoid undefined variable error
                if ERROR is None and answer_generator is not None:
                    # Stream the answer
                    with st.chat_message(ASSISTANT):
                        response_container = st.empty()
                        FULL_RESPONSE = ""

                        for chunk in answer_generator:
                            FULL_RESPONSE += chunk.content
                            response_container.markdown(FULL_RESPONSE + "▌")

                        response_container.markdown(FULL_RESPONSE)

                    elapsed_time = round((time.time() - time_start), 1)
                    logger.info("Elapsed time: %s sec.", elapsed_time)
                    logger.info("")

                    if config.ENABLE_USER_FEEDBACK:
                        st.session_state.get_feedback = True

                else:
                    st.error(ERROR)
                    FULL_RESPONSE = f"Error: {ERROR}"  # Set error message

                # Add user/assistant message to chat history (only if we have a response)
                if FULL_RESPONSE:
                    add_to_chat_history(HumanMessage(content=question))
                    add_to_chat_history(AIMessage(content=FULL_RESPONSE))

                # get the feedback
                if st.session_state.get_feedback:
                    st.feedback("stars", key="feedback", on_change=register_feedback)

            except Exception as e:
                ERR_MSG = f"Error in assistant_ui, generate_and_exec {e}"
                logger.error(ERR_MSG)
                st.error(ERR_MSG)

    except Exception as e:
        ERR_MSG = "An error occurred: " + str(e)
        logger.error(ERR_MSG)
        st.error(ERR_MSG)

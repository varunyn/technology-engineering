"""
File name: config.py
Author: Luigi Saetta
Date last modified: 2026-01-23
Last updated by: Varun Yadav
Python Version: 3.11

Description:
    This module provides all configurations for the RAG agent.
    
    IMPORTANT: Copy this file to config.py and fill in your actual values.
    config.py is in .gitignore and will NOT be committed to git.

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

# ============================================================================
# GENERAL SETTINGS
# ============================================================================
DEBUG = False
AUTH = "API_KEY"
OCI_PROFILE = "CHICAGO"

# ============================================================================
# OCI GENERAL CONFIGURATION
# ============================================================================
REGION = "us-chicago-1"
COMPARTMENT_ID = "ocid1.compartment.oc1..your-compartment-ocid"
SERVICE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

# ============================================================================
# LLM CONFIGURATION
# ============================================================================
LLM_MODEL_ID = "meta.llama-3.3-70b-instruct"
TEMPERATURE = 0.1
MAX_TOKENS = 4000

# Available models by region
if REGION == "us-chicago-1":
    MODEL_LIST = [
        "xai.grok-3",
        "xai.grok-4",
        "openai.gpt-4.1",
        "openai.gpt-4o",
        "openai.gpt-5",
        "meta.llama-3.3-70b-instruct",
        "cohere.command-a-03-2025",
    ]
else:
    MODEL_LIST = [
        "meta.llama-3.3-70b-instruct",
        "cohere.command-a-03-2025",
        "openai.gpt-4.1",
        "openai.gpt-4o",
        "openai.gpt-5",
    ]

# ============================================================================
# EMBEDDING MODEL CONFIGURATION
# ============================================================================
EMBED_MODEL_TYPE = "OCI"  # Options: "OCI" or "NVIDIA"
EMBED_MODEL_ID = "cohere.embed-multilingual-v3.0"
NVIDIA_EMBED_MODEL_URL = "http://your-nvidia-endpoint:8000/v1/embeddings"

# ============================================================================
# ORACLE VECTOR STORE (DATABASE) CONFIGURATION
# ============================================================================
VECTOR_DB_USER = "YOUR_DB_USERNAME"
VECTOR_DB_PWD = "YOUR_DB_PASSWORD"
VECTOR_WALLET_PWD = "YOUR_WALLET_PASSWORD"
VECTOR_DSN = "YOUR_DSN_NAME"
VECTOR_WALLET_DIR = "/path/to/your/wallet/directory"

CONNECT_ARGS = {
    "user": VECTOR_DB_USER,
    "password": VECTOR_DB_PWD,
    "dsn": VECTOR_DSN,
    "config_dir": VECTOR_WALLET_DIR,
    "wallet_location": VECTOR_WALLET_DIR,
    "wallet_password": VECTOR_WALLET_PWD,  # Required to avoid PEM passphrase prompt
}

# ============================================================================
# SEMANTIC SEARCH CONFIGURATION
# ============================================================================
TOP_K = 6
COLLECTION_LIST = ["DOCUMENT_CHUNKS_VS"]
DEFAULT_COLLECTION = "DOCUMENT_CHUNKS_VS"

# ============================================================================
# DOCUMENT PROCESSING CONFIGURATION
# ============================================================================
CHUNK_SIZE = 4000
CHUNK_OVERLAP = 100

# ============================================================================
# CONVERSATION HISTORY CONFIGURATION
# ============================================================================
MAX_MSGS_IN_HISTORY = 6  # Put -1 to disable trimming

# ============================================================================
# UI CONFIGURATION
# ============================================================================
LANGUAGE_LIST = ["same as the question", "en", "fr", "it", "es"]
ENABLE_USER_FEEDBACK = True

# ============================================================================
# MCP SERVER CONFIGURATION
# ============================================================================
TRANSPORT = "streamable-http"  # Options: "streamable-http" or "stdio"
HOST = "0.0.0.0"
PORT = 9000

# ============================================================================
# JWT AUTHENTICATION CONFIGURATION
# ============================================================================
ENABLE_JWT_TOKEN = False

# Simple JWT (HS256) - Used when ENABLE_JWT_TOKEN = True and NOT using OCI IAM
JWT_SECRET = "your-secret-key-here"
JWT_ALGORITHM = "HS256"  # For production, use RS256 with a key-pair

# OCI IAM JWT Configuration - ONLY needed if ENABLE_JWT_TOKEN = True and using OCI IAM
IAM_BASE_URL = "https://idcs-xxxxxxxxxxxxxxxxxxxxxxxxxxxx.identity.oraclecloud.com"
ISSUER = "https://identity.oraclecloud.com/"
AUDIENCE = ["urn:opc:lbaas:logicalguid=your-guid-here"]
OCI_CLIENT_ID = ""  # Client ID from OCI IAM confidential application
SECRET_OCID = ""    # OCID of secret in OCI Vault containing the client secret

# ============================================================================
# APPLICATION PERFORMANCE MONITORING (APM) CONFIGURATION
# ============================================================================
ENABLE_TRACING = False
AGENT_NAME = "OCI_CUSTOM_RAG_AGENT"
APM_CONTENT_TYPE = "application/json"
APM_BASE_URL = "https://your-apm-endpoint.apm-agt.region.oci.oraclecloud.com/20200101"
APM_PUBLIC_KEY = ""

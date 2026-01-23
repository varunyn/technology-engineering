# Custom RAG Agent

A production-ready **Retrieval-Augmented Generation (RAG)** agent built with **LangGraph**, **Oracle 23AI Vector Store**, and **OCI Generative AI**. This agent implements an advanced multi-step workflow for intelligent document Q&A with streaming responses.

**Author**: L. Saetta  
**Reviewed**: 23.09.2025

## Overview

This application provides an intelligent question-answering system that:
- Processes user queries through a multi-stage pipeline
- Searches documents using semantic vector search
- Reranks results using LLM-based relevance scoring
- Generates contextual answers with citations
- Supports streaming responses and real-time UI updates

## Architecture

```mermaid
graph TB
    subgraph "User Interface"
        UI[Streamlit Web UI]
    end
    
    subgraph "LangGraph Agent Workflow"
        START[Start] --> MOD[Content Moderation]
        MOD --> QR[Query Rewriter]
        QR --> VS[Vector Search]
        VS --> RERANK[Reranker]
        RERANK --> AG[Answer Generator]
        AG --> END[End]
    end
    
    subgraph "Data Layer"
        DB[(Oracle 23AI<br/>Vector Database)]
        VS --> DB
    end
    
    subgraph "AI Services"
        OCI_LLM[OCI Generative AI<br/>LLM]
        OCI_EMB[OCI Generative AI<br/>Embeddings]
        QR --> OCI_LLM
        RERANK --> OCI_LLM
        AG --> OCI_LLM
        VS --> OCI_EMB
    end
    
    UI --> START
    AG --> UI
    
    style MOD fill:#e1f5ff
    style QR fill:#e1f5ff
    style VS fill:#e1f5ff
    style RERANK fill:#e1f5ff
    style AG fill:#e1f5ff
    style DB fill:#fff4e1
    style OCI_LLM fill:#ffe1f5
    style OCI_EMB fill:#ffe1f5
```

## Workflow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Mod as Content Moderation
    participant QR as Query Rewriter
    participant VS as Vector Search
    participant DB as Oracle 23AI DB
    participant Rerank as Reranker
    participant AG as Answer Generator
    participant LLM as OCI GenAI LLM
    
    User->>UI: Submit Question
    UI->>Mod: Check Content
    Mod->>QR: Pass Query + History
    QR->>LLM: Reformulate Query
    LLM-->>QR: Standalone Question
    QR->>VS: Search Query
    VS->>DB: Vector Similarity Search
    DB-->>VS: Top K Documents
    VS->>Rerank: Candidate Documents
    Rerank->>LLM: Rank by Relevance
    LLM-->>Rerank: Ranked Documents
    Rerank->>AG: Filtered Documents
    AG->>LLM: Generate Answer
    LLM-->>AG: Stream Response
    AG-->>UI: Stream Answer + Citations
    UI-->>User: Display Results
```

## Key Components

### 1. **Content Moderation** (`content_moderation.py`)
- Validates user input for inappropriate content
- First line of defense before processing

### 2. **Query Rewriter** (`query_rewriter.py`)
- Reformulates user queries using chat history
- Converts contextual questions into standalone queries
- Example: "What about that?" → "What is Oracle 23AI?"

### 3. **Semantic Search** (`vector_search.py`)
- Performs vector similarity search in Oracle 23AI
- Uses embedding model to find relevant document chunks
- Returns top K most similar documents

### 4. **Reranker** (`reranker.py`)
- Uses LLM to evaluate and rank retrieved documents
- Filters out irrelevant results
- Improves answer quality by focusing on best matches

### 5. **Answer Generator** (`answer_generator.py`)
- Generates final answer using retrieved context
- Includes citations to source documents
- Supports streaming for real-time responses

### 6. **State Management** (`agent_state.py`)
- Manages workflow state across all nodes
- Tracks: user request, chat history, documents, answers, errors

## Data Flow

```
User Query
    ↓
[Content Moderation] → Validates input
    ↓
[Query Rewriter] → Reformulates using history
    ↓
[Vector Search] → Finds similar documents
    ↓
[Reranker] → Filters & ranks documents
    ↓
[Answer Generator] → Creates final answer
    ↓
Streamlit UI → Displays answer + citations
```

## Technology Stack

- **Framework**: LangGraph (agent orchestration)
- **Vector Database**: Oracle 23AI with VECTOR data type
- **LLM**: OCI Generative AI (Meta Llama, Cohere, OpenAI models)
- **Embeddings**: OCI Generative AI (Cohere multilingual)
- **UI**: Streamlit
- **Observability**: OCI APM (optional, via py-zipkin)
- **Language**: Python 3.11

## Setup

### Prerequisites

1. **Oracle 23AI Database** with:
   - Vector Store enabled
   - Table: `DOCUMENT_CHUNKS_VS` (created automatically)
   - Wallet configured for secure connection

2. **OCI Account** with:
   - Generative AI service access
   - API keys configured in `~/.oci/config`
   - Compartment with Generative AI permissions

3. **Python 3.11**

### Installation

This project uses `uv` for package management with `pyproject.toml` as the source of truth.

```bash
# Install uv (if not already installed)
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: pip install uv

# Sync project dependencies (creates .venv, installs all dependencies, generates uv.lock)
uv sync

# Activate virtual environment (optional - uv run handles this automatically)
source .venv/bin/activate

# Alternative: Install from requirements.txt (for backward compatibility)
# uv pip install -r requirements.txt
```

**Note**: The project uses `pyproject.toml` for dependency management. The `requirements.txt` file is kept for backward compatibility but `pyproject.toml` is the authoritative source.

**Development dependencies**:
```bash
# Install with development tools (pytest, black, ruff, mypy)
uv sync --group dev
```

### Configuration

**IMPORTANT**: Copy `config_template.py` to `config.py` and fill in your actual values. The `config.py` file is in `.gitignore` and will not be committed to git.

1. **Create your configuration file**:
   ```bash
   cp config_template.py config.py
   ```

2. **Database Configuration** (in `config.py`):
   ```python
   VECTOR_DB_USER = "your_user"
   VECTOR_DB_PWD = "your_password"
   VECTOR_DSN = "your_dsn"
   VECTOR_WALLET_DIR = "/path/to/wallet"
   VECTOR_WALLET_PWD = "wallet_password"
   ```

3. **OCI Configuration** (in `config.py`):
   ```python
   OCI_PROFILE = "CHICAGO"  # Your OCI config profile
   COMPARTMENT_ID = "ocid1.compartment..."
   REGION = "us-chicago-1"
   ```

4. **Model Configuration** (in `config.py`):
   ```python
   LLM_MODEL_ID = "meta.llama-3.3-70b-instruct"
   EMBED_MODEL_ID = "cohere.embed-multilingual-v3.0"
   COLLECTION_LIST = ["DOCUMENT_CHUNKS_VS"]
   ```

## Usage

### 1. Populate Knowledge Base

```bash
# Process PDF files
python scripts/populate_document_chunks_vs.py --files "document1.pdf" "document2.pdf"

# Process URLs
python scripts/populate_document_chunks_vs.py --urls "https://docs.oracle.com" "https://example.com"

# Process scraped data
python scripts/populate_document_chunks_vs.py --api-url "http://api-endpoint/v1/crawl/..."
```

### 2. Run the Application

```bash
streamlit run ui/assistant_ui_langgraph.py
```

The application will be available at `http://localhost:8501` (or next available port).

### 3. Query the Knowledge Base

1. Enter your question in the chat interface
2. The agent processes through all workflow stages
3. View intermediate results in the sidebar:
   - Standalone question (after rewriting)
   - References (after reranking)
4. Receive streaming answer with citations

## Features

### ✨ Streaming Responses
- Real-time answer generation
- Progressive UI updates as each stage completes
- Immediate display of document references

### 🔄 Chat History
- Maintains conversation context
- Automatically reformulates follow-up questions
- Configurable history length

### 🎯 Intelligent Reranking
- LLM-based relevance scoring
- Filters out irrelevant documents
- Improves answer accuracy

### 📊 Observability (Optional)
- OCI APM integration for tracing
- Performance monitoring
- Error tracking

### 🔒 Security
- Content moderation
- Wallet-based database authentication
- OCI IAM integration support

## MCP (Model Context Protocol) Integration

The application includes **MCP server** support, allowing LLM agents to interact with the vector database through standardized tools. This enables external agents (like Claude Desktop, custom LLM applications) to perform semantic search and query your knowledge base.

### MCP Architecture

```mermaid
graph TB
    subgraph "LLM Agent / Client"
        LLM[LLM Agent<br/>Claude/Custom App]
        CLIENT[MCP Client]
    end
    
    subgraph "MCP Server"
        SERVER[MCP Server<br/>FastMCP]
        AUTH{JWT Auth<br/>Optional}
        TOOLS[MCP Tools]
    end
    
    subgraph "Tools Available"
        T1[semantic_search]
        T2[get_collections]
        T3[list_documents_in_collection]
    end
    
    subgraph "Data Layer"
        DB[(Oracle 23AI<br/>Vector Database)]
        EMB[Embedding Model]
    end
    
    LLM -->|"1. User Query"| CLIENT
    CLIENT -->|"2. Tool Call Request<br/>(with JWT if enabled)"| SERVER
    SERVER -->|"3. Validate Token"| AUTH
    AUTH -->|"4. Authenticated"| TOOLS
    TOOLS -->|"5. Execute Tool"| T1
    TOOLS -->|"5. Execute Tool"| T2
    TOOLS -->|"5. Execute Tool"| T3
    T1 -->|"6. Query"| DB
    T1 -->|"6. Generate Embeddings"| EMB
    EMB -->|"7. Vector Search"| DB
    DB -->|"8. Results"| T1
    T1 -->|"9. Tool Response"| SERVER
    SERVER -->|"10. JSON Response"| CLIENT
    CLIENT -->|"11. Formatted Answer"| LLM
    
    style LLM fill:#e1f5ff
    style CLIENT fill:#e1f5ff
    style SERVER fill:#fff4e1
    style AUTH fill:#ffe1f5
    style TOOLS fill:#fff4e1
    style DB fill:#e1ffe1
    style EMB fill:#ffe1f5
```

### MCP User Flow

```mermaid
sequenceDiagram
    participant User
    participant LLM as LLM Agent
    participant Client as MCP Client
    participant Server as MCP Server
    participant Auth as JWT Auth<br/>(Optional)
    participant DB as Oracle Vector DB
    participant Embed as Embedding Model
    
    User->>LLM: Ask Question
    LLM->>Client: Discover Available Tools
    Client->>Server: list_tools()
    Server-->>Client: Tool Schemas
    
    LLM->>Client: Call semantic_search(query)
    Client->>Server: POST /mcp/ (with JWT if enabled)
    
    alt JWT Enabled
        Server->>Auth: Validate Token
        Auth-->>Server: Token Valid
    end
    
    Server->>Embed: Generate Embeddings
    Embed-->>Server: Query Vector
    Server->>DB: Vector Similarity Search
    DB-->>Server: Top K Documents
    Server-->>Client: JSON Response
    Client-->>LLM: Tool Results
    LLM->>LLM: Generate Answer
    LLM-->>User: Final Answer with Context
```

### MCP Tools

The MCP server exposes three main tools:

1. **`semantic_search`** - Search for relevant documents
   - Parameters: `query`, `top_k`, `collection_name` (optional)
   - Returns: Relevant document chunks with metadata

2. **`get_collections`** - List available collections
   - Returns: List of vector table names in the database

3. **`list_documents_in_collection`** - List documents in a collection
   - Parameters: `collection_name` (optional)
   - Returns: List of unique document sources with chunk counts

### Using MCP

See detailed documentation in:
- `MCP-QUICK-START.md` - Quick start guide
- `docs/MCP-USAGE.md` - Comprehensive usage guide

## Project Structure

```
custom-rag-agent/
├── src/
│   └── rag_agent/               # Core RAG agent package
│       ├── __init__.py
│       ├── agent_state.py       # State management
│       ├── rag_agent.py         # LangGraph workflow definition
│       ├── content_moderation.py # Content validation
│       ├── query_rewriter.py    # Query reformulation
│       ├── vector_search.py     # Semantic search
│       ├── reranker.py          # Document reranking
│       ├── answer_generator.py  # Answer generation
│       ├── prompts.py          # Prompt templates
│       ├── infrastructure/      # Infrastructure components
│       │   ├── __init__.py
│       │   ├── oci_models.py   # OCI GenAI integration
│       │   ├── db_utils.py     # Database utilities
│       │   ├── transport.py   # APM transport
│       │   ├── jwt_utils.py    # JWT utilities
│       │   ├── oci_jwt_client.py # OCI JWT client
│       │   └── custom_rest_embeddings.py # Custom embeddings
│       └── utils/              # Utility functions
│           ├── __init__.py
│           ├── utils.py        # General utilities
│           └── rag_feedback.py # Feedback handling
├── ui/                          # User interface
│   ├── __init__.py
│   ├── assistant_ui_langgraph.py # Streamlit UI
│   └── ui_mcp_agent.py         # MCP UI
├── api/                         # API endpoints
│   ├── __init__.py
│   └── rag_agent_api.py        # FastAPI REST API
├── scripts/                     # Utility scripts
│   ├── __init__.py
│   ├── populate_document_chunks_vs.py # Data ingestion
│   ├── chunk_index_utils.py    # Chunking utilities
│   ├── bm25_search.py          # BM25 search
│   └── llm_with_mcp.py         # MCP integration
├── mcp_servers/                 # MCP server implementations
│   ├── __init__.py
│   ├── mcp_semantic_search.py  # Semantic search MCP (HTTP)
│   ├── mcp_semantic_search_stdio.py # Semantic search MCP (STDIO)
│   ├── mcp_semantic_search_with_iam.py # Semantic search MCP (with IAM)
│   ├── mcp_servers_config.py   # MCP server config
│   ├── mcp_explorer.py         # MCP explorer utility
│   └── minimal_mcp_server.py   # Minimal MCP server example
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_mcp_semantic_search.py
│   ├── test_mcp_list_collection.py
│   ├── test_mcp_list_collection_with_oci_iam.py
│   ├── test_iam_for_jwt.py
│   ├── nvidia_test01.py
│   └── nvidia_test02.py
├── docs/                        # Documentation
│   ├── README.md               # Main documentation (this file)
│   ├── DATABASE-SETUP.md       # Database setup guide
│   ├── MCP-USAGE.md            # MCP usage guide
│   ├── MCP-TESTING.md          # MCP testing guide
│   └── REQUIREMENTS-ANALYSIS.md # Requirements analysis
├── config.py                    # Application configuration (gitignored)
├── config_template.py          # Config template (safe to commit)
├── pyproject.toml              # Project metadata and dependencies (uv)
├── .python-version              # Python version pin (3.11)
├── requirements.txt            # Dependencies (backward compatibility)
├── uv.lock                     # Lockfile (generated by uv sync)
├── test_mcp_simple.py          # Simple MCP test script
├── start_ui_mcp.sh             # Script to start MCP UI
├── MCP-QUICK-START.md          # Quick start guide for MCP
└── .gitignore                  # Git ignore rules
```

## Advantages of Agentic Approach

The modular LangGraph architecture provides:

1. **Flexibility**: Easy to add/remove/modify workflow steps
2. **Observability**: Each step can be monitored independently
3. **Error Handling**: Graceful degradation at each stage
4. **Extensibility**: Simple to add features like:
   - PII detection and anonymization
   - Multi-language support
   - Custom filtering logic
   - Additional validation steps

## Example Workflow Execution

```
User: "What is Oracle 23AI?"

1. [Moderator] ✓ Content validated
2. [QueryRewrite] → "What is Oracle 23AI?" (no history, no change)
3. [Search] → Found 6 relevant document chunks
4. [Rerank] → Ranked and filtered to top 3 chunks
5. [Answer] → Generated answer with citations:
   
   "Oracle 23AI is Oracle's next-generation database..."
   
   References:
   - DeepSeek.pdf (chunk 1)
   - Oracle Docs (page 5)
```

## Troubleshooting

See:
- `DATABASE-SETUP.md` - Database configuration
- `OCI-AUTH-SETUP.md` - OCI authentication
- `TROUBLESHOOTING-OCI-AUTH.md` - Common OCI errors

## License

MIT License

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Oracle 23AI Vector Search](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/)
- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/generative-ai/)
- [Integration with OCI APM](https://luigi-saetta.medium.com/enhancing-observability-in-rag-solutions-with-oracle-cloud-6f93b2675f40)

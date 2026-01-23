# Requirements Analysis

## Summary
- **Original requirements.txt**: 230 dependencies
- **Optimized requirements.txt**: 32 core dependencies
- **Reduction**: ~86% fewer explicit dependencies
- **Status**: Now using single optimized `requirements.txt` (requirements-minimal.txt and requirements_relaxed.txt removed)

## What Was Removed

### 1. Jupyter Ecosystem (NOT needed for Streamlit app)
- `ipykernel`, `ipython`, `ipython_pygments_lexers`, `ipywidgets`
- `jupyter`, `jupyter-console`, `jupyter-events`, `jupyter-lsp`
- `jupyter_client`, `jupyter_core`, `jupyter_server`, `jupyter_server_terminals`
- `jupyterlab`, `jupyterlab_pygments`, `jupyterlab_server`, `jupyterlab_widgets`
- `notebook`, `notebook_shim`
- `nbclient`, `nbconvert`, `nbformat`
- **Reason**: These are for Jupyter notebooks, not needed for the Streamlit web app

### 2. Development Tools (NOT needed for runtime)
- `black` (code formatter)
- `isort` (import sorter)
- `pylint` (linter)
- `mypy-extensions` (type checking)
- `debugpy` (debugger)
- **Reason**: These are development tools, not runtime dependencies

### 3. Visualization (Probably not needed)
- `matplotlib`, `matplotlib-inline`
- `altair`, `pydeck` (Streamlit charting - but Streamlit includes these)
- **Reason**: Streamlit has built-in charting, matplotlib may not be used

### 4. Redundant PDF Libraries
- Multiple PDF processing libraries: `pdfminer.six`, `pdfplumber`, `pypdf`, `pypdfium2`, `PyMuPDF`
- **Note**: `langchain-unstructured` handles PDFs, so these may be redundant

### 5. Unused Document Formats
- `python-docx` (Word docs - may be optional)
- `python-oxmsg` (Outlook - probably not needed)
- **Reason**: Check if these formats are actually used

### 6. Other Potentially Unnecessary
- `faiss-cpu` (vector search - but using Oracle Vector DB)
- `langgraph-prebuilt`, `langgraph-sdk` (may not be needed)
- `langsmith` (LangChain monitoring - optional)
- Many transitive dependencies that will be installed automatically

## Core Dependencies (What You Actually Need)

### Essential
1. **Streamlit** - Web UI
2. **LangChain ecosystem** - RAG functionality
   - `langchain`, `langchain-core`, `langchain-community`
   - `langchain-text-splitters`, `langchain-unstructured`
3. **LangGraph** - Agent framework
   - `langgraph`, `langgraph-checkpoint`
4. **Oracle** - Database and Cloud
   - `oracledb`, `oci`
5. **Observability** - `py-zipkin`
6. **Auth** - `PyJWT`
7. **HTTP** - `requests`, `httpx`
8. **Data** - `numpy`, `rank-bm25`
9. **Config** - `python-dotenv`

### Optional (for MCP features)
- `fastapi`, `fastmcp`, `mcp`, `starlette`

## Current Status

✅ **Optimized**: Single `requirements.txt` file with 32 core dependencies
✅ **Tested**: Verified in fresh virtual environment - all imports working
✅ **Compatible**: Works with both `uv` and `pip` package managers

## Installation

```bash
# Using uv (recommended - faster)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Using pip (traditional)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Note

The optimized `requirements.txt` includes only direct dependencies. Transitive dependencies (dependencies of dependencies) are automatically resolved and installed by the package manager.

# Requirements Analysis

## Summary
- **Original requirements.txt**: 229 dependencies
- **Minimal requirements-minimal.txt**: ~30 core dependencies
- **Reduction**: ~87% fewer explicit dependencies

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

## Recommendation

1. **For production**: Use `requirements-minimal.txt` and let pip resolve transitive dependencies
2. **For development**: Keep original `requirements.txt` if you need Jupyter/notebooks
3. **Test**: Create a fresh venv with minimal requirements and verify the app works

## Next Steps

1. Test `requirements-minimal.txt` in a fresh virtual environment
2. Remove any remaining unused dependencies
3. Consider splitting into:
   - `requirements.txt` (core)
   - `requirements-dev.txt` (development tools)
   - `requirements-optional.txt` (MCP, monitoring, etc.)

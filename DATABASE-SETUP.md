# Database Setup Requirements

## Overview

Yes, you're correct! The RAG agent requires **Oracle Vector Store** (23AI) database tables with vector embeddings of your documents. The app expects at least one collection (table) with vector data.

## Required Database Setup

### 1. Oracle Vector Store Database

You need:
- **Oracle Database 23c** or later with Vector Store capabilities
- A database user with appropriate permissions
- Connection configured in `config_private.py`:
  - `VECTOR_DB_USER`
  - `VECTOR_DB_PWD`
  - `VECTOR_DSN`
  - `VECTOR_WALLET_DIR` and `VECTOR_WALLET_PWD` (for secure connections)

### 2. Required Table Structure

Each collection (table) must have:
- A **VECTOR** column type for embeddings
- A **METADATA** column (JSON) containing document information
- The metadata should include a `source` field with the document name

Example table structure (Oracle 23AI):
```sql
CREATE TABLE BOOKS (
    ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    VECTOR VECTOR(1536, FLOAT32),  -- Embedding dimension depends on your model
    METADATA JSON,                 -- Contains: {"source": "document_name.pdf", "page_label": "1"}
    TEXT CLOB                      -- The actual text content (optional but recommended)
);
```

### 3. Default Collections

The app is configured to use these collections (see `config.py`):
- **BOOKS** (default)
- **NVIDIA_BOOKS2**
- **CNAF** (commented out)

You can modify `COLLECTION_LIST` in `config.py` to match your actual table names.

### 4. Loading Data into Collections

The app includes utilities to load documents:

#### Available Functions (in `chunk_index_utils.py`):
- `load_and_split_pdf(book_path)` - Loads and chunks PDF files
- `load_and_split_docx(file_path)` - Loads and chunks DOCX files

#### Adding Documents to a Collection:

You can use the `SemanticSearch.add_documents()` method:

```python
from vector_search import SemanticSearch
from chunk_index_utils import load_and_split_pdf

# Load and split a PDF
docs = load_and_split_pdf("path/to/document.pdf")

# Add to collection
search = SemanticSearch()
search.add_documents(docs, collection_name="BOOKS")
```

### 5. What the App Expects

The app will:
1. **List collections**: Automatically discovers tables with `VECTOR` columns using `db_utils.list_collections()`
2. **Search in collections**: Performs semantic search using the vector embeddings
3. **Extract metadata**: Reads the `source` field from JSON metadata to identify documents
4. **List books**: Uses `db_utils.list_books_in_collection()` to show available documents

### 6. Optional: Feedback Table

The app can create a feedback table automatically (`RAG_FEEDBACK`) if you enable user feedback in the UI. This table stores user ratings of answers.

## Current Status

Based on your `config_private.py`, you have:
- Database: `skwn23ai_medium`
- User: `Varun`
- Wallet configured at: `/Users/varuyada/.oracle/wallet`

## Next Steps

1. **Verify your database connection** - Test with `db_utils.list_collections()`
2. **Check if BOOKS table exists** - The app expects at least one collection
3. **Load your documents** - If BOOKS is empty, you need to load documents:
   ```python
   # Example script to load documents
   from vector_search import SemanticSearch
   from chunk_index_utils import load_and_split_pdf
   
   search = SemanticSearch()
   docs = load_and_split_pdf("your_document.pdf")
   search.add_documents(docs, "BOOKS")
   ```

## Troubleshooting

- **No collections found**: Make sure you have tables with `VECTOR` columns
- **Empty search results**: Your collection might be empty - load documents first
- **Connection errors**: Verify wallet path and credentials in `config_private.py`

## Note

The "BOOKS" name is just a convention - you can use any table name. Just update `COLLECTION_LIST` in `config.py` to match your actual table names.

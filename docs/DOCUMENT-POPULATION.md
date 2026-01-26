# Document Population Guide

This guide explains how to populate the vector database with documents using the `populate_document_chunks_vs.py` script.

## Overview

The `populate_document_chunks_vs.py` script processes local files and populates the `DOCUMENT_CHUNKS_VS` table in Oracle 23AI Vector Database. It extracts text content, chunks it using Oracle's `VECTOR_CHUNKS` function, generates embeddings, and stores them in the database.

## What It Does

1. **File Processing**: Extracts text content from various file formats (PDF, HTML, TXT, MD)
2. **Text Cleaning**: Removes navigation elements and low-quality content
3. **Chunking**: Uses Oracle's `VECTOR_CHUNKS` function to create semantic chunks
4. **Quality Filtering**: Filters chunks based on length and content quality
5. **Embedding Generation**: Creates embeddings using OCI Generative AI embedding models
6. **Database Storage**: Stores chunks with embeddings in `DOCUMENT_CHUNKS_VS` table
7. **File Archival**: Copies processed files to `uploaded_files/` directory for reference

## Supported File Formats

- **PDF** - Via Docling or unstructured library
- **HTML/HTM** - Via Docling or unstructured library
- **TXT** - Plain text files
- **MD/MARKDOWN** - Markdown files

## Prerequisites

1. Database connection configured in `config.py`
2. OCI Generative AI credentials configured
3. Embedding model ID set in `config.py`
4. Required dependencies installed (see `pyproject.toml`)

## Usage

### Basic Usage

```bash
# Process single file
python scripts/populate_document_chunks_vs.py --files "document.pdf"

# Process multiple files
python scripts/populate_document_chunks_vs.py --files "doc1.pdf" "doc2.html" "notes.txt" "readme.md"
```

### Command Line Arguments

- `--files` (required): One or more file paths to process

### Examples

```bash
# Process a PDF document
python scripts/populate_document_chunks_vs.py --files "report.pdf"

# Process multiple documents
python scripts/populate_document_chunks_vs.py --files "document.pdf" "page.html" "notes.txt" "readme.md"
```

## How It Works

1. **File Input**: Script accepts file paths via `--files` argument
2. **Content Extraction**: 
   - Uses Docling (if available) for advanced processing of PDF, DOCX, PPTX, etc.
   - Falls back to unstructured library for PDF and HTML
   - Direct file reading for TXT and MD files
3. **Text Processing**:
   - Cleans text by removing navigation elements
   - Validates content quality (length, meaningful words, etc.)
4. **Chunking**: Uses Oracle `VECTOR_CHUNKS` function with optimal parameters:
   - Chunk size: 200 words
   - Overlap: 20 words
   - Recursive splitting by sentences
5. **Embedding**: Generates embeddings in batches of 96 chunks using OCI Generative AI
6. **Storage**: Inserts chunks with embeddings into `DOCUMENT_CHUNKS_VS` table
7. **File Archival**: Copies original files to `uploaded_files/` directory with unique names

## Output

- **Database**: Chunks stored in `DOCUMENT_CHUNKS_VS` table with:
  - Text content
  - Embeddings (vector)
  - Metadata (source URL, file name, chunk offset, etc.)
- **Files**: Original files copied to `uploaded_files/` directory
- **Console**: Progress updates and summary of inserted chunks

## Configuration

Key settings in `config.py`:
- `EMBED_MODEL_ID`: Embedding model to use
- `COMPARTMENT_ID`: OCI compartment ID
- `CONNECT_ARGS`: Database connection parameters

## Notes

- Files are copied to `uploaded_files/` directory for reference in citations
- The script uses batch processing (96 chunks at a time) for efficient embedding generation
- Quality filtering ensures only meaningful content chunks are stored
- Supports retry logic for OCI service high-load scenarios

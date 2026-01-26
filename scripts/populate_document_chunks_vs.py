#!/usr/bin/env python3
"""
Populate DOCUMENT_CHUNKS_VS table using Oracle VECTOR_CHUNKS
Adapted from create_knowledge_base_enhanced.py to work with DOCUMENT_CHUNKS_VS schema
"""

import sys
import os
import shutil
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

import uuid

# Try to import unstructured for document processing
try:
    from unstructured.partition.html import partition_html
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("⚠️  unstructured not available")

# Try to import Docling for advanced document processing
try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    if not UNSTRUCTURED_AVAILABLE:
        print("⚠️  Neither Docling nor unstructured available - file processing will be limited")

import oci
import oracledb
import json
import re
from decimal import Decimal
from datetime import datetime

# Import configs from the custom-rag-agent
import config

# OCI Configuration
oci_config = oci.config.from_file(profile_name=config.OCI_PROFILE)
generative_ai_inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=oci_config,
    service_endpoint=config.SERVICE_ENDPOINT,
    retry_strategy=oci.retry.NoneRetryStrategy(),
    timeout=(10, 240)
)

TABLE_NAME = "DOCUMENT_CHUNKS_VS"
UPLOADED_FILES_DIR = "uploaded_files"

def get_project_root():
    """Get the project root directory (parent of scripts/)"""
    script_dir = Path(__file__).parent.absolute()
    return script_dir.parent

def ensure_uploaded_files_dir():
    """Ensure the uploaded_files directory exists"""
    project_root = get_project_root()
    uploaded_dir = project_root / UPLOADED_FILES_DIR
    uploaded_dir.mkdir(exist_ok=True)
    return uploaded_dir

def copy_file_to_uploaded(file_path):
    """
    Copy file to uploaded_files directory with a unique name.
    Returns the relative path to the copied file.
    """
    try:
        uploaded_dir = ensure_uploaded_files_dir()
        original_path = Path(file_path)
        
        # Generate unique filename: original_name_uuid.extension
        file_stem = original_path.stem
        file_ext = original_path.suffix
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{file_stem}_{unique_id}{file_ext}"
        
        # Copy file
        destination = uploaded_dir / new_filename
        shutil.copy2(file_path, destination)
        
        # Return relative path from project root
        project_root = get_project_root()
        relative_path = destination.relative_to(project_root)
        
        print(f"📋 Copied file to: {relative_path}")
        return str(relative_path)
        
    except Exception as e:
        print(f"⚠️  Warning: Could not copy file to uploaded_files: {e}")
        # Fallback to original path
        return f"file://{file_path}"

def create_db_connection():
    """Create database connection using config_private settings"""
    connection = oracledb.connect(**config.CONNECT_ARGS)
    return connection

def clean_text(text):
    """Enhanced text cleaning with better filtering"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common navigation elements
    navigation_patterns = [
        r'Skip to main content',
        r'Table of Contents',
        r'Navigation',
        r'Menu',
        r'Footer',
        r'Header',
        r'Breadcrumb',
        r'Pagination',
        r'Previous',
        r'Next'
    ]
    
    for pattern in navigation_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove empty lines and excessive whitespace again
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
    
    return text.strip()

def is_quality_content(text, min_length=100, max_length=8000):
    """Check if content is of good quality for embedding"""
    if not text or len(text) < min_length:
        return False
    
    if len(text) > max_length:
        return False
    
    # Check for too many links (navigation-heavy content)
    link_count = len(re.findall(r'\[.*?\]\(.*?\)', text))
    if link_count > 5:  # Too many links indicates navigation
        return False
    
    # Check for repetitive content
    words = text.split()
    if len(words) < 20:  # Too short
        return False
    
    # Check for meaningful content (not just headers/links)
    meaningful_words = len([w for w in words if len(w) > 3])
    if meaningful_words < 10:  # Not enough meaningful content
        return False
    
    # Check for common low-quality patterns
    low_quality_patterns = [
        r'^\s*[\*\-]\s*$',  # Just bullet points
        r'^\s*\[\s*\]\s*$',  # Empty links
        r'^\s*[A-Z\s]+\s*$',  # Just uppercase headers
    ]
    
    for pattern in low_quality_patterns:
        if re.match(pattern, text, re.MULTILINE):
            return False
    
    return True

def chunk_text_with_oracle_vector_chunks(cursor, text, chunk_size=200, overlap=20):
    """
    Use Oracle's VECTOR_CHUNKS function with optimal strategy for documentation content
    """
    try:
        chunk_sql = f"""
            SELECT chunk_offset, chunk_length, chunk_text
            FROM VECTOR_CHUNKS(:text 
                BY WORDS 
                MAX {chunk_size} 
                OVERLAP {overlap} 
                SPLIT BY RECURSIVELY 
                LANGUAGE AMERICAN 
                NORMALIZE ALL)
            WHERE LENGTH(chunk_text) > 50
        """
        
        cursor.execute(chunk_sql, text=text)
        
        chunks = []
        for row in cursor:
            chunk_offset, chunk_length, chunk_text = row
            cleaned_chunk = clean_text(chunk_text)
            
            if is_quality_content(cleaned_chunk):
                chunks.append({
                    'content': cleaned_chunk,
                    'offset': chunk_offset,
                    'length': chunk_length
                })
        
        print(f"Oracle VECTOR_CHUNKS created {len(chunks)} quality chunks")
        return chunks
        
    except Exception as e:
        print(f"Error using Oracle VECTOR_CHUNKS: {e}")
        # Fallback to simple chunking
        return fallback_chunking(text)

def fallback_chunking(text):
    """Fallback chunking method if VECTOR_CHUNKS fails"""
    chunks = []
    words = text.split()
    chunk_size = 200
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        cleaned_chunk = clean_text(chunk_text)
        
        if is_quality_content(cleaned_chunk):
            chunks.append({
                'content': cleaned_chunk,
                'offset': i + 1,
                'length': len(chunk_text)
            })
    
    return chunks

def process_file_content(cursor, file_path, use_docling=True):
    """Process a file and extract content for embedding"""
    chunks = []
    
    try:
        print(f"📁 Processing file: {file_path}")
        
        # Copy file to uploaded_files directory
        stored_file_path = copy_file_to_uploaded(file_path)
        
        file_ext = file_path.lower().split('.')[-1]
        
        if use_docling and DOCLING_AVAILABLE:
            supported_docling_formats = ['pdf', 'docx', 'pptx', 'xlsx', 'html', 'htm', 'png', 'jpg', 'jpeg', 'tiff']
            if file_ext in supported_docling_formats:
                print(f"🔬 Using Docling for advanced processing of {file_ext.upper()} file")
                converter = DocumentConverter()
                result = converter.convert(file_path)
                text_content = result.document.export_to_markdown()
                if text_content:
                    print(f"✅ Docling extracted content: {len(text_content)} characters")
                else:
                    text_content = None
            else:
                text_content = None
        else:
            text_content = None
        
        if not text_content:
            if file_ext == 'pdf':
                if UNSTRUCTURED_AVAILABLE:
                    elements = partition_pdf(filename=file_path)
                    text_content = '\n\n'.join([elem.text for elem in elements if hasattr(elem, 'text') and elem.text])
                else:
                    print(f"⚠️  unstructured not available for PDF processing")
                    return chunks
            elif file_ext in ['html', 'htm']:
                if UNSTRUCTURED_AVAILABLE:
                    elements = partition_html(filename=file_path)
                    text_content = '\n\n'.join([elem.text for elem in elements if hasattr(elem, 'text') and elem.text])
                else:
                    print(f"⚠️  unstructured not available for HTML processing")
                    return chunks
            elif file_ext in ['txt', 'md', 'markdown']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            else:
                print(f"⚠️  Unsupported file type: {file_ext}")
                return chunks
        
        if not text_content or len(text_content.strip()) < 100:
            print(f"⚠️  No meaningful content in file: {file_path}")
            return chunks
        
        cleaned_text = clean_text(text_content)
        
        # Chunk first, then filter by quality (don't check entire document)
        oracle_chunks = chunk_text_with_oracle_vector_chunks(cursor, cleaned_text)
        
        original_filename = Path(file_path).name
        for chunk in oracle_chunks:
            chunks.append({
                'content': chunk['content'],
                'metadata': {
                    'source_type': 'file',
                    'source_url': stored_file_path,
                    'file_name': original_filename,
                    'chunk_offset': chunk['offset'],
                    'chunk_length': chunk['length']
                },
                'chunk_offset': chunk['offset'],
                'chunk_length': chunk['length']
            })
        
        print(f"✅ Created {len(chunks)} quality chunks from file: {file_path}")
        
    except Exception as e:
        print(f"❌ Error processing file {file_path}: {str(e)}")
    
    return chunks

def insert_data(cursor, chunk_id, text, embedding, metadata):
    """Insert data into DOCUMENT_CHUNKS_VS table"""
    try:
        # Convert metadata to JSON string, handling Decimal
        class DecimalEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                return super().default(obj)
        
        metadata_json = json.dumps(metadata, cls=DecimalEncoder) if metadata else '{}'
        
        cursor.setinputsizes(None, None, None, oracledb.DB_TYPE_VECTOR)
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} (id, text, metadata, embedding)
            VALUES (:1, :2, :3, :4)
        """, [chunk_id, text, metadata_json, embedding])
        
    except Exception as e:
        print(f"Error inserting data: {str(e)}")
        raise

def populate_from_files(files):
    """Populate DOCUMENT_CHUNKS_VS from files"""
    connection = create_db_connection()
    cursor = connection.cursor()
    
    print(f"Populating {TABLE_NAME} table...")
    
    all_chunks = []
    
    if files:
        print(f"\n📁 Processing {len(files)} file(s)...")
        for file_path in files:
            file_chunks = process_file_content(cursor, file_path)
            all_chunks.extend(file_chunks)
    
    if not all_chunks:
        print("❌ No quality chunks found")
        cursor.close()
        connection.close()
        return
    
    print(f"\n📊 Processing {len(all_chunks)} total chunks for embedding...")
    
    # Process chunks in batches for embedding
    start = 0
    inserted_count = 0
    
    while start < len(all_chunks):
        embed_text_detail = oci.generative_ai_inference.models.EmbedTextDetails()
        content_subsets = all_chunks[start:start+96]
        inputs = []
        metadata_list = []
        
        for subset in content_subsets:
            if subset and 'content' in subset:
                inputs.append(subset['content'])
                metadata_list.append(subset.get('metadata', {}))
        
        if not inputs:
            start += 96
            continue
        
        embed_text_detail.inputs = inputs
        embed_text_detail.model_id = config.EMBED_MODEL_ID
        embed_text_detail.compartment_id = config.COMPARTMENT_ID
        embed_text_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=config.EMBED_MODEL_ID)
        
        try:
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    response = generative_ai_inference_client.embed_text(embed_text_detail)
                    embeddings = response.data.embeddings
                    break
                except Exception as e:
                    retry_count += 1
                    if "high load" in str(e).lower() and retry_count < max_retries:
                        print(f"OCI service experiencing high load, retrying in {retry_count * 2} seconds...")
                        import time
                        time.sleep(retry_count * 2)
                    else:
                        raise e
            
            batch_size = min(len(embeddings), len(inputs))
            
            for i in range(batch_size):
                try:
                    chunk_id = str(uuid.uuid4())[:64]  # VARCHAR2(64) compatible
                    insert_data(cursor, chunk_id, inputs[i], list(embeddings[i]), metadata_list[i])
                    inserted_count += 1
                except Exception as e:
                    print(f"Error inserting item {i}: {str(e)}")
                    continue
            
            connection.commit()
                    
        except Exception as e:
            print(f"Error while creating embeddings: {e}")
            start += 96
            continue
        
        start += 96
        print(f"Processed batch: {start}/{len(all_chunks)} items ({inserted_count} inserted)")
    
    cursor.close()
    connection.close()
    print(f"\n✅ Successfully populated {TABLE_NAME} with {inserted_count} embeddings")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Populate DOCUMENT_CHUNKS_VS table from files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process files
  python populate_document_chunks_vs.py --files "document.pdf" "page.html" "text.txt" "readme.md"
        """
    )
    
    parser.add_argument('--files', nargs='+', required=True, help='File path(s) to process (PDF, HTML, TXT, MD)')
    
    args = parser.parse_args()
    
    populate_from_files(files=args.files)

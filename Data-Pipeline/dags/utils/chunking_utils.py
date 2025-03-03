"""
Utility functions for chunking text documents.
"""

from typing import List
import logging

def chunk_text(text: str, min_chars: int = 1000) -> List[str]:
    """
    Split text into chunks based on paragraphs, ensuring minimum length.
    
    Args:
        text: Text content to chunk
        min_chars: Minimum characters per chunk
        
    Returns:
        List of text chunks
    """
    # Split by paragraphs (double newline)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    # For paragraphs that are too short, combine them
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < min_chars:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
    
    if current_chunk:  # Don't forget the last chunk
        chunks.append(current_chunk)
    
    logging.info(f"Split text into {len(chunks)} chunks")
    return chunks

def chunk_text_from_file(file_path: str, min_chars: int = 1000) -> List[str]:
    """
    Read a file and split its content into chunks.
    
    Args:
        file_path: Path to the text file
        min_chars: Minimum characters per chunk
        
    Returns:
        List of text chunks
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return chunk_text(content, min_chars)
    except Exception as e:
        logging.error(f"Error chunking file {file_path}: {str(e)}")
        # Return the whole file as a single chunk if there's an error
        with open(file_path, 'r', encoding='utf-8') as file:
            return [file.read()]
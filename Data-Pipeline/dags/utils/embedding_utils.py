"""
Utility functions for generating embeddings.
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

# Cache for loaded models
_MODEL_CACHE = {}

def get_embedding_model(model_name: str) -> SentenceTransformer:
    """
    Get a cached embedding model or load it if not available.
    
    Args:
        model_name: Name of the model to load
        
    Returns:
        Loaded SentenceTransformer model
    """
    if model_name not in _MODEL_CACHE:
        logging.info(f"Loading embedding model: {model_name}")
        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]

def generate_embedding(text: str, model_name: str) -> np.ndarray:
    """
    Generate embedding for a text using the specified model.
    
    Args:
        text: Text to embed
        model_name: Name of the model to use
        
    Returns:
        Numpy array with embedding
    """
    model = get_embedding_model(model_name)
    return model.encode(text)

def process_file(
    file_path: str, 
    model_name: str, 
    enable_chunking: bool = False, 
    chunk_size: int = 1000
) -> List[Dict[str, Any]]:
    """
    Process a file and generate embeddings.
    
    Args:
        file_path: Path to the file
        model_name: Name of the embedding model
        enable_chunking: Whether to chunk the file
        chunk_size: Minimum characters per chunk
        
    Returns:
        List of dictionaries with text and embeddings
    """
    from .chunking_utils import chunk_text_from_file
    
    file_id = os.path.basename(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        embeddings_data = []
        
        if enable_chunking:
            chunks = chunk_text_from_file(file_path, chunk_size)
            
            for i, chunk in enumerate(chunks):
                embedding = generate_embedding(chunk, model_name)
                
                embeddings_data.append({
                    'id': f"{file_id}_{i}",
                    'text': chunk,
                    'embedding': embedding.tolist(),
                    'metadata': {
                        'source': file_path,
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                })
        else:
            # Process the whole file as one document
            embedding = generate_embedding(content, model_name)
            
            embeddings_data.append({
                'id': file_id,
                'text': content,
                'embedding': embedding.tolist(),
                'metadata': {
                    'source': file_path,
                }
            })
            
        return embeddings_data
            
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {str(e)}")
        return []

def save_embeddings(embeddings_data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Save embeddings to a JSON file.
    
    Args:
        embeddings_data: List of dictionaries with embeddings
        output_path: Path to save the JSON file
        
    Returns:
        Path to the saved file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f)
    
    logging.info(f"Saved {len(embeddings_data)} embeddings to {output_path}")
    return output_path

def load_embeddings(input_path: str) -> List[Dict[str, Any]]:
    """
    Load embeddings from a JSON file.
    
    Args:
        input_path: Path to the JSON file
        
    Returns:
        List of dictionaries with embeddings
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        embeddings_data = json.load(f)
    
    logging.info(f"Loaded {len(embeddings_data)} embeddings from {input_path}")
    return embeddings_data
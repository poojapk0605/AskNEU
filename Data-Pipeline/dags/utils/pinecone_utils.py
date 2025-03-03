"""
Utility functions for interacting with Pinecone.
"""

import logging
import pinecone
from typing import List, Dict, Any

def initialize_pinecone(api_key: str, environment: str) -> None:
    """
    Initialize Pinecone client.
    
    Args:
        api_key: Pinecone API key
        environment: Pinecone environment
    """
    pinecone.init(api_key=api_key, environment=environment)
    logging.info(f"Initialized Pinecone in environment: {environment}")

def upsert_vectors(
    index_name: str, 
    vectors: List[Dict[str, Any]], 
    namespace: str = '', 
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Upsert vectors to Pinecone index in batches.
    
    Args:
        index_name: Name of the Pinecone index
        vectors: List of vector dictionaries
        namespace: Pinecone namespace
        batch_size: Number of vectors per batch
        
    Returns:
        Dictionary with upsert statistics
    """
    index = pinecone.Index(index_name)
    total_vectors = len(vectors)
    stats = {
        'total_vectors': total_vectors,
        'total_batches': (total_vectors + batch_size - 1) // batch_size,
        'successful_vectors': 0,
        'failed_vectors': 0
    }
    
    for i in range(0, total_vectors, batch_size):
        batch = vectors[i:i + batch_size]
        try:
            upsert_response = index.upsert(
                vectors=batch,
                namespace=namespace
            )
            stats['successful_vectors'] += len(batch)
            logging.info(f"Upserted batch {i//batch_size + 1}/{stats['total_batches']}: {len(batch)} vectors")
        except Exception as e:
            stats['failed_vectors'] += len(batch)
            logging.error(f"Error upserting batch {i//batch_size + 1}/{stats['total_batches']}: {str(e)}")
    
    return stats
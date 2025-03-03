"""
Utility functions for configuration management.
"""

import logging
from typing import Dict, Any
from airflow.models import Variable
from ..config.default_config import DEFAULT_CONFIG

def get_config() -> Dict[str, Any]:
    """
    Get configuration from Airflow Variables, falling back to defaults.
    
    Returns:
        Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Storage config
    config['storage']['conn_id'] = Variable.get(
        'storage_connection_id', 
        default_var=config['storage']['conn_id']
    )
    config['storage']['bucket_name'] = Variable.get(
        'bucket_name', 
        default_var=config['storage']['bucket_name']
    )
    config['storage']['prefix'] = Variable.get(
        'source_prefix', 
        default_var=config['storage']['prefix']
    )
    config['storage']['local_path'] = Variable.get(
        'local_storage_path', 
        default_var=config['storage']['local_path']
    )
    
    # Pinecone config
    config['pinecone']['api_key'] = Variable.get(
        'pinecone_api_key', 
        default_var=config['pinecone']['api_key']
    )
    config['pinecone']['environment'] = Variable.get(
        'pinecone_environment', 
        default_var=config['pinecone']['environment']
    )
    config['pinecone']['index_name'] = Variable.get(
        'pinecone_index_name', 
        default_var=config['pinecone']['index_name']
    )
    config['pinecone']['namespace'] = Variable.get(
        'pinecone_namespace', 
        default_var=config['pinecone']['namespace']
    )
    
    # Embedding config
    config['embedding']['model_name'] = Variable.get(
        'embedding_model_name', 
        default_var=config['embedding']['model_name']
    )
    config['embedding']['chunk_size'] = int(Variable.get(
        'chunk_size', 
        default_var=config['embedding']['chunk_size']
    ))
    config['embedding']['enable_chunking'] = Variable.get(
        'enable_chunking', 
        default_var=str(config['embedding']['enable_chunking'])
    ).lower() in ('true', 't', '1', 'yes')
    
    # Processing config
    config['processing']['batch_size'] = int(Variable.get(
        'batch_size', 
        default_var=config['processing']['batch_size']
    ))
    config['processing']['max_batches'] = int(Variable.get(
        'max_batches', 
        default_var=config['processing']['max_batches']
    ))
    config['processing']['upsert_batch_size'] = int(Variable.get(
        'upsert_batch_size', 
        default_var=config['processing']['upsert_batch_size']
    ))
    
    return config
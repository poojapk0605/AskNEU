"""
Default configuration for the embedding pipeline.
These values can be overridden using Airflow Variables.
"""

DEFAULT_CONFIG = {
    'storage': {
        'conn_id': 'google_cloud_default',
        'bucket_name': 'your-gcp-bucket',
        'prefix': '',
        'local_path': '/tmp/airflow_data',
    },
    'pinecone': {
        'api_key': 'your-pinecone-api-key',
        'environment': 'your-pinecone-environment',
        'index_name': 'your-pinecone-index',
        'namespace': '',
    },
    'embedding': {
        'model_name': 'all-MiniLM-L6-v2',
        'chunk_size': 1000,  # Minimum characters per chunk
        'enable_chunking': False,  # Set to True to enable text chunking
    },
    'processing': {
        'batch_size': 100,  # Files per batch
        'max_batches': 4,   # Maximum number of batches
        'upsert_batch_size': 100,  # Vectors per Pinecone upsert operation
    }
}
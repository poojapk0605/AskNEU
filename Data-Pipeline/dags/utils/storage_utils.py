"""
Utility functions for interacting with GCP Cloud Storage.
"""

import os
import logging
from google.cloud import storage
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from typing import List, Dict, Any

def list_bucket_files(gcs_hook: GCSHook, bucket_name: str, prefix: str = '') -> List[str]:
    """
    List all files in a GCS bucket with the given prefix.
    
    Args:
        gcs_hook: Initialized GCSHook
        bucket_name: Name of the GCS bucket
        prefix: Optional prefix to filter objects
        
    Returns:
        List of file paths in the bucket
    """
    blobs = gcs_hook.list_blobs(bucket_name=bucket_name, prefix=prefix)
    
    # Filter out directories
    files = [blob.name for blob in blobs if not blob.name.endswith('/')]
    logging.info(f"Found {len(files)} files in bucket {bucket_name} with prefix {prefix}")
    return files

def download_files(
    gcs_hook: GCSHook, 
    bucket_name: str, 
    file_keys: List[str], 
    local_dir: str
) -> List[str]:
    """
    Download a list of files from GCS bucket to a local directory.
    
    Args:
        gcs_hook: Initialized GCSHook
        bucket_name: Name of the GCS bucket
        file_keys: List of file keys to download
        local_dir: Local directory to store downloaded files
        
    Returns:
        List of local file paths for downloaded files
    """
    os.makedirs(local_dir, exist_ok=True)
    downloaded_files = []
    
    for file_key in file_keys:
        # Create subdirectories if needed
        local_file_path = os.path.join(local_dir, os.path.basename(file_key))
        local_file_dir = os.path.dirname(local_file_path)
        if local_file_dir:
            os.makedirs(local_file_dir, exist_ok=True)
        
        # Download the file
        gcs_hook.download(
            bucket_name=bucket_name,
            object_name=file_key,
            filename=local_file_path
        )
        
        downloaded_files.append(local_file_path)
        logging.info(f"Downloaded {file_key} to {local_file_path}")
    
    return downloaded_files

def cleanup_local_directory(directory: str, simulate: bool = True) -> None:
    """
    Remove a local directory and all its contents.
    
    Args:
        directory: Directory to remove
        simulate: If True, only log what would be removed without actually removing
    """
    import shutil
    
    if simulate:
        logging.info(f"Would remove directory: {directory}")
    else:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            logging.info(f"Removed directory: {directory}")
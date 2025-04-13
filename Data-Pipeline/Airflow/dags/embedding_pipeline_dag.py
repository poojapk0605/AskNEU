from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import logging
import math
from typing import List, Dict, Any

# Import utilities
from src.kushal.utils.config_utils import get_config
from src.kushal.utils.storage_utils import (
    list_bucket_files,
    download_files,
    cleanup_local_directory,
)
from src.kushal.utils.embedding_utils import (
    process_file,
    save_embeddings,
    load_embeddings,
)
from src.kushal.utils.pinecone_utils import initialize_pinecone, upsert_vectors

# Default configurations
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "gcs_to_pinecone_embedding",
    default_args=default_args,
    description="Process files from GCS bucket, generate embeddings, and upsert to Pinecone",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 3, 1),
    catchup=False,
    tags=["embedding", "pinecone", "nlp", "gcp"],
)


# Task functions
def list_files_task(**kwargs):
    """List all files in the bucket and divide them into batches."""
    from airflow.providers.google.cloud.hooks.gcs import GCSHook

    config = get_config()
    storage_config = config["storage"]
    processing_config = config["processing"]

    # Connect to GCS
    gcs_hook = GCSHook(gcp_conn_id=storage_config["conn_id"])
    all_files = list_bucket_files(
        gcs_hook=gcs_hook,
        bucket_name=storage_config["bucket_name"],
        prefix=storage_config["prefix"],
    )

    total_files = len(all_files)

    # Calculate batch parameters
    batch_size = processing_config["batch_size"]
    max_batches = processing_config["max_batches"]

    # Adjust batch size if needed
    if total_files > batch_size * max_batches:
        batch_size = math.ceil(total_files / max_batches)
        logging.info(
            f"Adjusted batch size to {batch_size} to fit {total_files} files in {max_batches} batches"
        )

    # Create batches
    batches = []
    for i in range(0, total_files, batch_size):
        batch = all_files[i : i + batch_size]
        batches.append(batch)

    # Push batches to XCom
    kwargs["ti"].xcom_push(key="file_batches", value=batches)
    kwargs["ti"].xcom_push(key="total_files", value=total_files)
    kwargs["ti"].xcom_push(key="batch_count", value=len(batches))

    return len(batches)


def download_batch_task(batch_index, **kwargs):
    """Download a batch of files from the bucket."""
    from airflow.providers.google.cloud.hooks.gcs import GCSHook

    ti = kwargs["ti"]
    batches = ti.xcom_pull(task_ids="list_files", key="file_batches")

    if batch_index >= len(batches):
        logging.info(f"Batch {batch_index} does not exist. Skipping.")
        return []

    batch = batches[batch_index]
    config = get_config()
    storage_config = config["storage"]

    # Ensure local directory exists
    local_dir = os.path.join(storage_config["local_path"], f"batch_{batch_index}")

    # Connect to GCS and download files
    gcs_hook = GCSHook(gcp_conn_id=storage_config["conn_id"])
    downloaded_files = download_files(
        gcs_hook=gcs_hook,
        bucket_name=storage_config["bucket_name"],
        file_keys=batch,
        local_dir=local_dir,
    )

    # Push the list of downloaded files to XCom
    ti.xcom_push(key=f"downloaded_files_batch_{batch_index}", value=downloaded_files)
    return downloaded_files


def process_batch_task(batch_index, **kwargs):
    """Process a batch of files and generate embeddings."""
    ti = kwargs["ti"]
    downloaded_files = ti.xcom_pull(
        key=f"downloaded_files_batch_{batch_index}",
        task_ids=f"download_batch_{batch_index}",
    )
    config = get_config()

    model_name = config["embedding"]["model_name"]
    enable_chunking = config["embedding"]["enable_chunking"]
    chunk_size = config["embedding"]["chunk_size"]

    all_embeddings = []

    for file_path in downloaded_files:
        embeddings_data = process_file(
            file_path=file_path,
            model_name=model_name,
            enable_chunking=enable_chunking,
            chunk_size=chunk_size,
        )
        all_embeddings.extend(embeddings_data)

    # Save embeddings to a local file for the batch
    embeddings_dir = os.path.join(config["storage"]["local_path"], "embeddings")
    embeddings_path = os.path.join(
        embeddings_dir, f"embeddings_batch_{batch_index}.json"
    )

    save_embeddings(all_embeddings, embeddings_path)

    ti.xcom_push(key=f"embeddings_path_batch_{batch_index}", value=embeddings_path)
    return embeddings_path


def upsert_batch_task(batch_index, **kwargs):
    """Upsert embeddings to Pinecone."""
    ti = kwargs["ti"]
    embeddings_path = ti.xcom_pull(
        key=f"embeddings_path_batch_{batch_index}",
        task_ids=f"process_batch_{batch_index}",
    )
    config = get_config()

    pinecone_config = config["pinecone"]
    processing_config = config["processing"]

    # Initialize Pinecone
    initialize_pinecone(
        api_key=pinecone_config["api_key"], environment=pinecone_config["environment"]
    )

    # Load embeddings from file
    embeddings_data = load_embeddings(embeddings_path)

    # Prepare vectors for upsert
    vectors = []
    for item in embeddings_data:
        vectors.append(
            {
                "id": item["id"],
                "values": item["embedding"],
                "metadata": {
                    "text": item["text"][:1000],  # Limit text length for metadata
                    **item["metadata"],
                },
            }
        )

    # Upsert to Pinecone
    stats = upsert_vectors(
        index_name=pinecone_config["index_name"],
        vectors=vectors,
        namespace=pinecone_config["namespace"],
        batch_size=processing_config["upsert_batch_size"],
    )

    return f"Upserted {stats['successful_vectors']} vectors to Pinecone from batch {batch_index}"


def cleanup_task(**kwargs):
    """Cleanup temporary local files."""
    config = get_config()
    local_path = config["storage"]["local_path"]

    # Set to False to actually delete files, True for dry run
    cleanup_local_directory(local_path, simulate=True)

    return "Cleanup task completed"


# Create tasks
list_files_operator = PythonOperator(
    task_id="list_files",
    python_callable=list_files_task,
    provide_context=True,
    dag=dag,
)


# Dynamic task creation for batch processing
def create_batch_processing_tasks(dag):
    """Create download, process, and upsert tasks dynamically."""

    def create_download_task(batch_idx):
        return PythonOperator(
            task_id=f"download_batch_{batch_idx}",
            python_callable=download_batch_task,
            op_args=[batch_idx],
            provide_context=True,
            dag=dag,
        )

    def create_process_task(batch_idx):
        return PythonOperator(
            task_id=f"process_batch_{batch_idx}",
            python_callable=process_batch_task,
            op_args=[batch_idx],
            provide_context=True,
            dag=dag,
        )

    def create_upsert_task(batch_idx):
        return PythonOperator(
            task_id=f"upsert_batch_{batch_idx}",
            python_callable=upsert_batch_task,
            op_args=[batch_idx],
            provide_context=True,
            dag=dag,
        )

    # We'll create tasks for the maximum possible number of batches
    config = get_config()
    max_batches = config["processing"]["max_batches"]

    download_tasks = []
    process_tasks = []
    upsert_tasks = []

    for i in range(max_batches):
        download_task = create_download_task(i)
        process_task = create_process_task(i)
        upsert_task = create_upsert_task(i)

        # Set dependencies
        list_files_operator >> download_task >> process_task >> upsert_task

        download_tasks.append(download_task)
        process_tasks.append(process_task)
        upsert_tasks.append(upsert_task)

    return download_tasks, process_tasks, upsert_tasks


download_tasks, process_tasks, upsert_tasks = create_batch_processing_tasks(dag)

# Add cleanup task after all batches are processed
cleanup_operator = PythonOperator(
    task_id="cleanup",
    python_callable=cleanup_task,
    provide_context=True,
    dag=dag,
)

# Set cleanup to run after all upsert tasks
for upsert_task in upsert_tasks:
    upsert_task >> cleanup_operator

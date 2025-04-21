import logging
import os
import subprocess
import json
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any
from airflow import DAG
from airflow.exceptions import AirflowFailException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from google.cloud import storage
from google.oauth2 import service_account
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from urllib.parse import urlparse

# Configuration (Cleaned up)
SCRAPED_TEXT_DIR = "/opt/airflow/dags/src/scraped_texts"
GCS_BUCKET_NAME = "askneu"

# Securely fetching secrets from environment variables
GCP_SA_KEY = os.getenv("GCP_SA_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate that environment variables are provided
for var_name, var_value in {
    "GCP_SA_KEY": GCP_SA_KEY,
    "PINECONE_API_KEY": PINECONE_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY
}.items():
    if not var_value:
        raise ValueError(f"Missing required environment variable: {var_name}")

TMP_DIR = "/opt/airflow/tmp/embeddings"
BATCH_SIZE = 32
MAX_BATCHES = 10
DVC_REPO_PATH = "/opt/airflow/dags/src"
DVC_REMOTE_NAME = "gcs-store"
DVC_REMOTE_URL = f"gs://{GCS_BUCKET_NAME}/dvc-storage"

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,
    chunk_overlap=184
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "email_on_failure": True,
}

# Helper function to get GCP credentials securely
def get_gcp_credentials():
    credentials_dict = json.loads(GCP_SA_KEY)
    return service_account.Credentials.from_service_account_info(credentials_dict)

# Corrected upload_to_gcs function
def upload_to_gcs():
    credentials = get_gcp_credentials()
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    uploaded = []
    for file_name in os.listdir(SCRAPED_TEXT_DIR):
        if file_name.endswith(".txt"):
            blob = bucket.blob(f"scraped_texts/{file_name}")
            blob.upload_from_filename(os.path.join(SCRAPED_TEXT_DIR, file_name))
            uploaded.append(file_name)
    return uploaded

# Utility functions updated to use secure credentials
def setup_dvc():
    from pathlib import Path
    Path(SCRAPED_TEXT_DIR).mkdir(parents=True, exist_ok=True)
    Path(TMP_DIR).mkdir(parents=True, exist_ok=True)
    dvc_dir = Path(DVC_REPO_PATH) / ".dvc"
    if not dvc_dir.exists():
        subprocess.run(["dvc", "init", "--no-scm", "-f"], cwd=DVC_REPO_PATH, check=True)
    subprocess.run(["dvc", "remote", "add", "--default", DVC_REMOTE_NAME, DVC_REMOTE_URL],
                   cwd=DVC_REPO_PATH, check=True)

def version_data(path: str):
    from pathlib import Path
    if not Path(path).exists():
        raise AirflowFailException(f"Path {path} does not exist for versioning!")
    subprocess.run(["dvc", "add", path, "--external"], cwd=DVC_REPO_PATH, check=True)
    subprocess.run(["dvc", "push"], cwd=DVC_REPO_PATH, check=True)

def validate_scraped_text():
    files = [f for f in os.listdir(SCRAPED_TEXT_DIR) if f.endswith(".txt")]
    if not files:
        raise AirflowFailException("No .txt files found after scraping!")
    return len(files)

def list_and_batch_files():
    credentials = get_gcp_credentials()
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix="scraped_texts/"))
    files = [b.name for b in blobs if b.name.endswith(".txt")]
    for f in glob.glob(f"{TMP_DIR}/batch_*.json"):
        os.remove(f)
    os.makedirs(TMP_DIR, exist_ok=True)
    for batch_idx, i in enumerate(range(0, len(files), BATCH_SIZE)):
        with open(f"{TMP_DIR}/batch_{batch_idx}.json", "w") as f:
            json.dump(files[i:i + BATCH_SIZE], f)
    return len(files)

def process_batch(batch_idx: int):
    credentials = get_gcp_credentials()
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
    vector_store = PineconeVectorStore(index_name="airflowtest", embedding=embeddings, pinecone_api_key=PINECONE_API_KEY)

    batch_file = f"{TMP_DIR}/batch_{batch_idx}.json"
    if not os.path.exists(batch_file):
        return {"processed": 0, "failed": 0}

    with open(batch_file, "r") as f:
        file_paths = json.load(f)

    processed, failed = 0, 0
    for file_path in file_paths:
        try:
            blob = bucket.blob(file_path)
            content = blob.download_as_text()
            lines = content.split('\n')
            if len(lines) <= 4: continue
            source = lines[0].split("URL (Source): ")[1].strip()
            date_line = lines[1].split("Scraped on: ")[1].strip()
            remaining_text = '\n'.join(lines[2:])
            chunks = text_splitter.split_text(remaining_text)
            if not chunks: continue
            filename_stem = os.path.splitext(os.path.basename(file_path))[0]
            parsed_url = urlparse(source)
            subdomain = parsed_url.hostname.split('.')[0] if parsed_url.hostname else "Northeastern"
            unix_date = datetime.fromisoformat(date_line).timestamp()
            vector_store.add_texts(
                texts=chunks,
                metadatas=[{"source": source, "date": date_line, "unix_time": unix_date, "subdomain": subdomain} for _ in chunks],
                ids=[f"{filename_stem}_{i}" for i in range(len(chunks))]
            )
            processed += 1
        except Exception as e:
            logging.error(f"Error processing {file_path}: {str(e)}")
            failed += 1
    return {"processed": processed, "failed": failed}

# (Your existing DAG definition remains unchanged, as it's correct)


def get_email_summary():
    total_processed = 0
    total_failed = 0
    for result_file in glob.glob(f"{TMP_DIR}/result_*.json"):
        with open(result_file, "r") as f:
            result = json.load(f)
            total_processed += result.get("processed", 0)
            total_failed += result.get("failed", 0)

    return f"""
    <h3>Processing Summary</h3>
    <p>Successfully processed files: {total_processed}</p>
    <p>Failed files: {total_failed}</p>
    <p>Total files attempted: {total_processed + total_failed}</p>
    """

# DAG Definition
with DAG(
        dag_id="production_pipeline",
        default_args=default_args,
        schedule_interval="@daily",
        catchup=False,
) as dag:
    # Installation and setup tasks
    install_deps = BashOperator(
        task_id="install_deps",
        bash_command="pip install -r /opt/airflow/dags/src/requirements.txt dvc dvc-gs"
    )

    # New task to run unit tests
    run_unit_tests = BashOperator(
        task_id="run_unit_tests",
        bash_command="python /opt/airflow/dags/src/page_scrapper/test_scraper.py || true",
    )

    # DVC setup group
    with TaskGroup("dvc_setup_group") as dvc_setup_tasks:
        setup_dvc_task = PythonOperator(
            task_id="initialize_dvc",
            python_callable=setup_dvc
        )

    # Scraping tasks
    with TaskGroup("scraping_group") as scraping_tasks:
        scrape_data = BashOperator(
            task_id="scrape_data",
            bash_command=f"python /opt/airflow/dags/src/page_scrapper/Scrape_script.py"
        )
        validate = PythonOperator(
            task_id="validate_data",
            python_callable=validate_scraped_text
        )
        upload_gcs = PythonOperator(
            task_id="upload_gcs",
            python_callable=upload_to_gcs
        )

    # DVC versioning group
    with TaskGroup("dvc_versioning_group") as dvc_versioning_tasks:
        version_scraped_data = PythonOperator(
            task_id="version_scraped_data",
            python_callable=version_data,
            op_kwargs={"path": SCRAPED_TEXT_DIR}
        )
        version_processed_batches = PythonOperator(
            task_id="version_processed_batches",
            python_callable=version_data,
            op_kwargs={"path": TMP_DIR}
        )

    # Embedding tasks
    with TaskGroup("embedding_group") as embedding_tasks:
        list_files = PythonOperator(
            task_id="list_and_batch_files",
            python_callable=list_and_batch_files
        )
        process_tasks = []
        for i in range(MAX_BATCHES):
            task = PythonOperator(
                task_id=f"process_batch_{i}",
                python_callable=process_batch,
                op_kwargs={"batch_idx": i}
            )
            process_tasks.append(task)
        list_files >> process_tasks

    # Notification and cleanup
    email_summary = PythonOperator(
        task_id="prepare_email_summary",
        python_callable=get_email_summary
    )

    notifications = EmailOperator(
        task_id="send_email",
        to="chatbot.neu25@gmail.com",
        subject="Pipeline Summary",
        html_content="{{ ti.xcom_pull(task_ids='prepare_email_summary') }}",
    )

    cleanup = BashOperator(
        task_id="cleanup",
        bash_command=f"rm -rf {TMP_DIR}/*"
    )

    # Updated workflow dependencies
    install_deps >> run_unit_tests >> dvc_setup_tasks >> scrape_data
    scrape_data >> validate >> [upload_gcs, version_scraped_data]
    upload_gcs >> embedding_tasks
    version_scraped_data >> embedding_tasks
    embedding_tasks >> version_processed_batches
    version_processed_batches >> email_summary >> notifications >> cleanup
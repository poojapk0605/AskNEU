# Base Airflow Image
FROM apache/airflow:2.8.1-python3.9

# Set working directory to Airflow home
WORKDIR /opt/airflow

# Copy DAG files into the Airflow DAGs directory
COPY ["Data Pipeline/dags/", "/opt/airflow/dags/"]

# Install Python dependencies including requirements.txt, dvc, and dvc-gs
COPY ["Data Pipeline/dags/src/requirements.txt", "/opt/airflow/requirements.txt"]

RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt \
    && pip install --no-cache-dir dvc dvc-gs

# Ensure the Airflow user has proper permissions
USER airflow


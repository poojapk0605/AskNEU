# Use the official Apache Airflow image
FROM apache/airflow:2.8.1-python3.9

# Set working directory to Airflow's home
WORKDIR /opt/airflow

# Copy DAGs
COPY ./Data Pipeline/dags/ /opt/airflow/dags/

# Optional: Copy requirements.txt (if your DAGs have Python dependencies)
COPY ./Data Pipeline/dags/src/requirements.txt /opt/airflow/requirements.txt

# Install custom Python dependencies + DVC
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt \
    && pip install --no-cache-dir dvc dvc-gs

# Ensure port 8080 is exposed (Cloud Run requires)
EXPOSE 8080

# Use $PORT env variable from Cloud Run (defaults to 8080)
ENV PORT=8080
ENV AIRFLOW_HOME=/opt/airflow

# Start the Airflow webserver on 0.0.0.0:$PORT for Cloud Run compatibility
CMD ["sh", "-c", "airflow webserver --port $PORT --hostname 0.0.0.0"]
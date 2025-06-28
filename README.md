# 🧠 AskNEU – GCP-Deployed RAG Chatbot with Kubernetes & Airflow

AskNEU is a Retrieval-Augmented Generation (RAG) chatbot designed to answer questions using structured content scraped from Northeastern University websites. The project includes a fully automated data pipeline using Apache Airflow, embedding generation, vector storage with Pinecone, and deployment on GKE with Istio, GitHub Actions, and full-stack observability.

---

## 🧰 Tech Stack

- **Language:** Python, Bash
- **Orchestration:** Apache Airflow
- **Scraping:** Selenium
- **Vector DB:** Pinecone
- **Cloud:** GCP (GKE, GCS, DNS, Cloud NAT)
- **CI/CD:** GitHub Actions
- **Security:** Istio, Cert-Manager
- **Monitoring:** Prometheus, Grafana

---

## 🛠️ Key Features

- 🔄 Automated web scraping using Selenium
- 🧠 Embedding generation and semantic search with Pinecone
- ⚙️ DAG orchestration using Apache Airflow
- ☁️ Containerized deployment on GKE via GitHub Actions
- 🛡️ Secured ingress with Istio and TLS using Cert-Manager
- 📊 Real-time observability using Prometheus + Grafana

---

## ⚙️ Deployment Overview

1. **Data Pipeline:**
   - Airflow DAG scrapes content → stores raw HTML/text in GCS
   - DAG triggers embedding script → stores vectors in Pinecone

2. **Backend Deployment:**
   - Docker containers built and pushed via GitHub Actions
   - Deployed to GKE with Kubernetes manifests and Helm
   - Istio handles routing and TLS termination

3. **Monitoring:**
   - Metrics exported to Prometheus
   - Dashboards visualized in Grafana

---

## 📊 Diagram 
![image](https://github.com/user-attachments/assets/9953f038-09f0-48e7-9082-e17365088f13)

---

## 📦 Folder Structure

AskNEU/
├── airflow/
│ ├── dags/
│ ├── config/
├── deployment/
│ ├── Dockerfile
│ ├── k8s/
├── scraper/
├── embeddings/
├── README.md


---

## 🔗 Links

- 📂 GitHub Repo: [AskNEU](https://github.com/poojapk0605/AskNEU)  
- 🔗 [LinkedIn Profile](https://www.linkedin.com/in/poojakannanpk/)

---

## 📄 License  
MIT License

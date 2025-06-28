# 🧠 AskNEU – RAG-Based Chatbot on GCP with Kubernetes, Cloud Run & Airflow

AskNEU is a Retrieval-Augmented Generation (RAG) chatbot designed to answer questions using content scraped from Northeastern University websites. The project integrates a data pipeline using Apache Airflow, vector storage with Pinecone, and frontend/backend services deployed on Google Cloud Platform using GKE and Cloud Run. Authentication is secured with Google OAuth, and user data is stored in MongoDB Atlas.

---

## 🧰 Tech Stack

- **Languages:** Python, Bash
- **Data Pipeline:** Apache Airflow, Selenium
- **Vector Search:** Pinecone
- **Authentication:** Google OAuth 2.0 (gAuth)
- **Database:** MongoDB Atlas
- **Cloud Infrastructure:** Google Cloud Platform (GKE, Cloud Run, GCS, DNS, Static IP)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus, Grafana

---

## 🛠️ Key Features

- 🔄 Web scraping with Selenium + Airflow DAG orchestration  
- 🧠 Embedding generation and semantic vector storage using Pinecone  
- ⚙️ Frontend and chatbot API deployed on **Cloud Run**  
- 🐳 Airflow-based pipeline components deployed on **GKE**  
- 🔐 User authentication via **Google OAuth 2.0**  
- 💾 User login/session data stored in **MongoDB Atlas**  
- 🌐 Custom domain + static IP configured via GCP DNS  
- 📊 Prometheus + Grafana dashboards for full observability  
- 🔁 CI/CD integration with GitHub Actions

---

## ⚙️ Deployment Overview

### 🔹 Data Pipeline (GKE)
- Airflow DAGs orchestrate scraping, embedding, and chunking tasks
- Output stored in GCS and Pinecone

### 🔹 Chatbot Services (Cloud Run)
- Lightweight backend REST APIs served on Cloud Run
- Secured using OAuth2 login and integrated with MongoDB

### 🔹 Infrastructure Highlights
- Custom domain + static IP (GCP)
- IAM, TLS, and firewall rules for security
- Metrics pushed to Prometheus, visualized in Grafana

---

## 🗂️ Folder Structure

AskNEU/
├── airflow/ # DAGs for scraping & embedding
├── backend/ # Python chatbot and API services
├── deployment/ # Kubernetes & Cloud Run configs
├── scraper/ # Selenium-based scraper
├── README.md

---

## 📸 Screenshots & Architecture *(Add if available)*
![image](https://github.com/user-attachments/assets/9953f038-09f0-48e7-9082-e17365088f13)

---

## 🔗 Links

- 🔗 [Project Demo/Docs](https://drive.google.com/file/d/1BtBDYbpdjcrxSFbS0vBKKpWXjgVBblU_/view)
- 📂 [GitHub Repo](https://github.com/poojapk0605/AskNEU)  
- 📫 [Connect on LinkedIn](https://www.linkedin.com/in/poojakannanpk/)

---

## 📄 License  
This project is licensed under the [MIT License](./LICENSE)

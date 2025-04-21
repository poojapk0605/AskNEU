// providers.tf
terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.5"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.11"
    }
  }
}

provider "google" {
  project     = var.project_id
  credentials = file(var.credentials_file)
  region      = "us-central1"
  zone        = "us-central1-a"
}

provider "kubernetes" {
  host                   = module.gke_cluster.kubeconfig["host"]
  token                  = module.gke_cluster.kubeconfig["token"]
  cluster_ca_certificate = base64decode(module.gke_cluster.kubeconfig["cluster_ca_certificate"])
}

provider "helm" {
  kubernetes {
    host                   = module.gke_cluster.kubeconfig["host"]
    token                  = module.gke_cluster.kubeconfig["token"]
    cluster_ca_certificate = base64decode(module.gke_cluster.kubeconfig["cluster_ca_certificate"])
  }
}

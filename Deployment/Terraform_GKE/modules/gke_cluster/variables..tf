variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP Region to deploy the cluster"
}

variable "cluster_name" {
  type        = string
  description = "Name of the GKE cluster"
}

variable "machine_type" {
  type        = string
  description = "Machine type for the GKE nodes"
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "zone" {
  description = "GCP zone"
  type        = string
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
}
variable "machine_type" {
  description = "The type of machine to use for nodes"
  type        = string

}

variable "credentials_file" {

  type = string
}

# variable "kubeconfig_path" {
#   description = "Path to your kubeconfig file for accessing the GKE cluster"
#   type        = string
#   default     = "~/.kube/config" # or provide manually via terraform.tfvars or CLI
# }

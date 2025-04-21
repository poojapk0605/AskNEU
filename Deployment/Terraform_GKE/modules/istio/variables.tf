variable "project_id" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "location" {
  type = string
}

variable "kubeconfig" {
  description = "Kubeconfig information to authenticate with the cluster"
  type = object({
    host                   = string
    token                  = string
    cluster_ca_certificate = string
  })
}

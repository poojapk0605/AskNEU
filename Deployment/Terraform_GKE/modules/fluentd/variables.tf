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
  description = "Kubeconfig object for helm and k8s provider"
  type = object({
    host                   = string
    token                  = string
    cluster_ca_certificate = string
  })
}

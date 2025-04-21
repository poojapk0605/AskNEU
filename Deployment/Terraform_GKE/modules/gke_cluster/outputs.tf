data "google_client_config" "default" {}

output "kubeconfig" {
  value = {
    host                   = google_container_cluster.primary.endpoint
    cluster_ca_certificate = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
    token                  = data.google_client_config.default.access_token
  }
}

output "cluster_name" {
  value = google_container_cluster.primary.name
}

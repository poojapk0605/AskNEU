resource "google_container_cluster" "primary" {
  name               = var.cluster_name
  location           = var.region
  initial_node_count = 1

  remove_default_node_pool = true
  deletion_protection      = true

  node_config {
    machine_type = var.machine_type
    disk_type    = "pd-balanced" # ✅ Balanced persistent disk
    disk_size_gb = 100
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  lifecycle {
    prevent_destroy = false
    ignore_changes  = [initial_node_count]
  }
}

resource "google_container_node_pool" "default_pool" {
  name     = "app-node-pool"
  location = var.region
  cluster  = google_container_cluster.primary.name

  node_config {
    machine_type = var.machine_type
    disk_type    = "pd-balanced" # ✅ Balanced persistent disk here too
    disk_size_gb = 100
  }

  initial_node_count = 4

  # lifecycle {
  #   prevent_destroy = false
  # }
}

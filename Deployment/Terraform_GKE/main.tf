
module "gke_cluster" {
  source       = "./modules/gke_cluster"
  project_id   = var.project_id # 👈 passing it manually
  region       = var.zone
  cluster_name = var.cluster_name
  machine_type = var.machine_type
}


module "istio" {
  source       = "./modules/istio"
  project_id   = var.project_id
  cluster_name = module.gke_cluster.cluster_name
  location     = var.zone
  kubeconfig   = module.gke_cluster.kubeconfig
}

module "cert_manager" {
  source       = "./modules/cert-manager"
  project_id   = var.project_id
  cluster_name = module.gke_cluster.cluster_name
  location     = var.zone
  kubeconfig   = module.gke_cluster.kubeconfig
}

module "prometheus" {
  source       = "./modules/prometheus"
  project_id   = var.project_id
  cluster_name = module.gke_cluster.cluster_name
  location     = var.zone
  kubeconfig   = module.gke_cluster.kubeconfig
}


# module "grafana" {
#   source       = "./modules/grafana"
#   project_id   = var.project_id
#   cluster_name = module.gke_cluster.cluster_name
#   location     = var.zone
#   kubeconfig   = module.gke_cluster.kubeconfig
# }

# module "fluentd" {
#   source       = "./modules/fluentd"
#   project_id   = var.project_id
#   cluster_name = module.gke_cluster.cluster_name
#   location     = var.zone
#   kubeconfig   = module.gke_cluster.kubeconfig
# }

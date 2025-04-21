provider "helm" {
  kubernetes {
    host                   = var.kubeconfig["host"]
    token                  = var.kubeconfig["token"]
    cluster_ca_certificate = base64decode(var.kubeconfig["cluster_ca_certificate"])
  }
}

resource "helm_release" "prometheus" {
  name             = "prometheus"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "prometheus"
  namespace        = "monitoring" # ✅ Changed from "prometheus" to "monitoring"
  create_namespace = true

  values = [
    file("${path.module}/values.yaml")
  ]
}

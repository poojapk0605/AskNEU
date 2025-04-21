provider "helm" {
  kubernetes {
    host                   = var.kubeconfig["host"]
    token                  = var.kubeconfig["token"]
    cluster_ca_certificate = base64decode(var.kubeconfig["cluster_ca_certificate"])
  }
}

resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  version          = "v1.14.2" # ✅ You can pin a stable version
  namespace        = "cert-manager"
  create_namespace = true

  set {
    name  = "installCRDs"
    value = "true"
  }
}

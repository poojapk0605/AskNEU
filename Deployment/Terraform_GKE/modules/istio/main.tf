provider "helm" {
  kubernetes {
    host                   = var.kubeconfig["host"]
    token                  = var.kubeconfig["token"]
    cluster_ca_certificate = base64decode(var.kubeconfig["cluster_ca_certificate"])
  }
}

resource "helm_release" "istio_base" {
  name             = "istio-base"
  repository       = "https://istio-release.storage.googleapis.com/charts"
  chart            = "base"
  namespace        = "istio-system"
  create_namespace = true
}

resource "helm_release" "istiod" {
  name       = "istiod"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  namespace  = "istio-system"
  depends_on = [helm_release.istio_base]
}

resource "helm_release" "istio_ingress" {
  name       = "istio-ingress"
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "gateway"
  namespace  = "istio-system"
  depends_on = [helm_release.istiod]
}

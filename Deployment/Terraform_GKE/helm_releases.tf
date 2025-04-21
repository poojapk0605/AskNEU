

# ------------------------
# Istio Installation
# ------------------------

# resource "helm_release" "istio_base" {
#   name             = "istio-base"
#   repository       = "https://istio-release.storage.googleapis.com/charts"
#   chart            = "base"
#   namespace        = "istio-system"
#   create_namespace = true
#   version          = "1.21.1"
# }

# resource "helm_release" "istiod" {
#   name             = "istiod"
#   repository       = "https://istio-release.storage.googleapis.com/charts"
#   chart            = "istiod"
#   namespace        = "istio-system"
#   create_namespace = false
#   version          = "1.21.1"
#   depends_on       = [helm_release.istio_base]
# }

# resource "helm_release" "istio_ingress" {
#   name             = "istio-ingressgateway"
#   repository       = "https://istio-release.storage.googleapis.com/charts"
#   chart            = "gateway"
#   namespace        = "istio-ingress"
#   create_namespace = true
#   version          = "1.21.1"
#   depends_on       = [helm_release.istiod]
# }

# ------------------------
# Monitoring Stack
# ------------------------

# resource "helm_release" "prometheus" {
#   name             = "prometheus"
#   repository       = "https://prometheus-community.github.io/helm-charts"
#   chart            = "prometheus"
#   namespace        = "monitoring"
#   create_namespace = true
#   version          = "25.8.0"
# }

# resource "helm_release" "grafana" {
#   name             = "grafana"
#   repository       = "https://grafana.github.io/helm-charts"
#   chart            = "grafana"
#   namespace        = "monitoring"
#   version          = "7.3.9"
#   create_namespace = false

#   values = [
#     file("${path.module}/modules/grafana/values.yaml")
#   ]

#   depends_on = [helm_release.prometheus]
# }

# resource "helm_release" "fluent-bit" {
#   name             = "fluent-bit"
#   repository       = "https://charts.bitnami.com/bitnami"
#   chart            = "fluent-bit"
#   namespace        = "monitoring"
#   create_namespace = false
#   version          = "2.4.4" # You can change to the latest if needed

#   values = [
#     file("${path.module}/modules/fluentd/values.yaml")
#   ]
# }
# ------------------------
# Cert-Manager
# ------------------------

# resource "helm_release" "cert_manager" {
#   name             = "cert-manager"
#   repository       = "https://charts.jetstack.io"
#   chart            = "cert-manager"
#   namespace        = "cert-manager"
#   version          = "v1.13.2"
#   create_namespace = true

#   set {
#     name  = "installCRDs"
#     value = true
#   }
# }

# ------------------------
# Frontend & Proxy Apps
# ------------------------

resource "helm_release" "frontend" {
  name             = "neu-frontend"
  chart            = "${path.module}/k8s-manifests/frontend-helm"
  namespace        = "frontend"
  create_namespace = true

  values = [
    file("${path.module}/k8s-manifests/frontend-helm/values.yaml")
  ]
}

resource "helm_release" "proxy" {
  name             = "vertex-proxy"
  chart            = "${path.module}/k8s-manifests/proxy-helm"
  namespace        = "proxy"
  create_namespace = true

  values = [
    file("${path.module}/k8s-manifests/proxy-helm/values.yaml")
  ]
}

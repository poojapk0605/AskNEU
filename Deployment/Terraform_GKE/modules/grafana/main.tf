resource "helm_release" "grafana" {
  name             = "grafana"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "grafana"
  namespace        = "monitoring"
  version          = "7.3.10"
  create_namespace = false

  values = [
    file("${path.module}/values.yaml")
  ]
}

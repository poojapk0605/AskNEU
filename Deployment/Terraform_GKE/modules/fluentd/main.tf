resource "helm_release" "fluentd" {
  name       = "fluentd"
  namespace  = "monitoring"
  chart      = "fluent-bit"
  repository = "https://kiwigrid.github.io"

  values = [file("${path.module}/values.yaml")]
}

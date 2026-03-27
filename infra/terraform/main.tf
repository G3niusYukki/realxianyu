# XianyuFlow v10 Phase 1 - Infrastructure as Code
# Terraform configuration for Kind cluster and Helm releases

terraform {
  required_version = ">= 1.0"
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

# Kubernetes provider configuration
provider "kubernetes" {
  config_path = "~/.kube/config"
}

# Helm provider configuration
provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

# XianyuFlow namespace
resource "kubernetes_namespace" "xianyuflow" {
  metadata {
    name = "xianyuflow"
  }
}

# Redis Cluster Helm Release
resource "helm_release" "redis" {
  name       = "redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis-cluster"
  version    = "9.1.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../helm/xianyuflow-infra/values-redis.yaml")
  ]

  depends_on = [kubernetes_namespace.xianyuflow]
}

# PostgreSQL Helm Release
resource "helm_release" "postgresql" {
  name       = "postgresql"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql-ha"
  version    = "12.0.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../helm/xianyuflow-infra/values-postgres.yaml")
  ]

  depends_on = [kubernetes_namespace.xianyuflow]
}

# Kafka Helm Release
resource "helm_release" "kafka" {
  name       = "kafka"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kafka"
  version    = "26.4.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../helm/xianyuflow-infra/values-kafka.yaml")
  ]

  depends_on = [kubernetes_namespace.xianyuflow]
}

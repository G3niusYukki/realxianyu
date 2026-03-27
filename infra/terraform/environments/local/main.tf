terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11.0"
    }
  }
}

# Kind provider
provider "kind" {}

# Create Kind cluster
resource "kind_cluster" "xianyuflow" {
  name           = var.cluster_name
  wait_for_ready = true

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"

      extra_port_mappings {
        container_port = 80
        host_port      = 8080
      }

      extra_port_mappings {
        container_port = 443
        host_port      = 8443
      }
    }

    node {
      role = "worker"
    }

    node {
      role = "worker"
    }
  }
}

# Kubernetes provider configuration
provider "kubernetes" {
  host                   = kind_cluster.xianyuflow.endpoint
  cluster_ca_certificate = kind_cluster.xianyuflow.cluster_ca_certificate
  client_certificate     = kind_cluster.xianyuflow.client_certificate
  client_key             = kind_cluster.xianyuflow.client_key
}

# Helm provider configuration
provider "helm" {
  kubernetes {
    host                   = kind_cluster.xianyuflow.endpoint
    cluster_ca_certificate = kind_cluster.xianyuflow.cluster_ca_certificate
    client_certificate     = kind_cluster.xianyuflow.client_certificate
    client_key             = kind_cluster.xianyuflow.client_key
  }
}

# Create xianyuflow namespace
resource "kubernetes_namespace" "xianyuflow" {
  metadata {
    name = "xianyuflow"
  }

  depends_on = [kind_cluster.xianyuflow]
}

# Create monitoring namespace
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }

  depends_on = [kind_cluster.xianyuflow]
}

# Redis Cluster Helm Release
resource "helm_release" "redis" {
  name       = "redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis-cluster"
  version    = "9.0.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../../../helm/xianyuflow-infra/values-redis.yaml")
  ]

  set_sensitive {
    name  = "password"
    value = var.redis_password
  }

  depends_on = [kubernetes_namespace.xianyuflow]
}

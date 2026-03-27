# XianyuFlow v10 - Phase 1: 基础设施实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 搭建完整的云原生基础设施，包括 Kubernetes 集群、数据库、缓存、消息队列和可观测性栈

**Architecture:** 使用 Terraform 管理基础设施即代码，部署高可用的 K8s 集群（本地 Kind 用于开发，EKS 用于生产），集成 PostgreSQL、Redis Cluster、Kafka 和监控栈

**Tech Stack:** Terraform, Kind/K3s/EKS, Helm, PostgreSQL, Redis, Kafka, Prometheus, Grafana, Jaeger

---

## 文件结构

```
infra/
├── terraform/
│   ├── modules/
│   │   ├── kubernetes/      # K8s 集群模块
│   │   ├── database/        # PostgreSQL 模块
│   │   ├── cache/           # Redis 模块
│   │   ├── messaging/       # Kafka 模块
│   │   └── monitoring/      # 监控栈模块
│   ├── environments/
│   │   ├── local/           # 本地开发环境 (Kind)
│   │   └── production/      # 生产环境 (EKS)
│   └── main.tf
├── helm/
│   └── xianyuflow-infra/    # 基础设施 Helm Chart
├── docker/
│   └── base-images/         # 基础镜像定义
└── scripts/
    ├── setup-local.sh       # 本地环境一键启动
    └── migrate-data.sh      # 数据迁移脚本
```

---

## Task 1: 创建项目结构和 Terraform 基础配置

**Files:**
- Create: `infra/terraform/environments/local/main.tf`
- Create: `infra/terraform/environments/local/variables.tf`
- Create: `infra/terraform/environments/local/outputs.tf`
- Create: `infra/terraform/modules/kubernetes/main.tf`
- Create: `infra/terraform/modules/kubernetes/variables.tf`

**Step 1: 创建本地开发环境目录结构**

```bash
mkdir -p infra/terraform/{modules/{kubernetes,database,cache,messaging,monitoring},environments/{local,production}}
mkdir -p infra/helm infra/docker/base-images infra/scripts
```

**Step 2: 创建本地环境主配置**

```hcl
# infra/terraform/environments/local/main.tf
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

provider "kind" {}

# 创建 Kind 集群
resource "kind_cluster" "xianyuflow" {
  name           = "xianyuflow-local"
  node_image     = "kindest/node:v1.28.0"
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

      kubeadm_config_patches = [
        "kind: InitConfiguration\nnodeRegistration:\n  kubeletExtraArgs:\n    node-labels: \"ingress-ready=true\""
      ]
    }

    node {
      role = "worker"
    }

    node {
      role = "worker"
    }
  }
}

# 配置 Kubernetes 提供者
provider "kubernetes" {
  host                   = kind_cluster.xianyuflow.endpoint
  cluster_ca_certificate = kind_cluster.xianyuflow.cluster_ca_certificate
  client_certificate     = kind_cluster.xianyuflow.client_certificate
  client_key             = kind_cluster.xianyuflow.client_key
}

provider "helm" {
  kubernetes {
    host                   = kind_cluster.xianyuflow.endpoint
    cluster_ca_certificate = kind_cluster.xianyuflow.cluster_ca_certificate
    client_certificate     = kind_cluster.xianyuflow.client_certificate
    client_key             = kind_cluster.xianyuflow.client_key
  }
}

# 部署命名空间
resource "kubernetes_namespace" "xianyuflow" {
  metadata {
    name = "xianyuflow"
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }
}
```

**Step 3: 创建变量定义**

```hcl
# infra/terraform/environments/local/variables.tf
variable "cluster_name" {
  description = "Kind cluster name"
  type        = string
  default     = "xianyuflow-local"
}

variable "postgres_password" {
  description = "PostgreSQL admin password"
  type        = string
  default     = "xianyu2024"
  sensitive   = true
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  default     = "xianyu2024"
  sensitive   = true
}
```

**Step 4: 创建输出定义**

```hcl
# infra/terraform/environments/local/outputs.tf
output "cluster_name" {
  description = "Kind cluster name"
  value       = kind_cluster.xianyuflow.name
}

output "kubeconfig_path" {
  description = "Path to kubeconfig"
  value       = "${path.module}/kubeconfig"
}

output "namespaces" {
  description = "Created namespaces"
  value       = [kubernetes_namespace.xianyuflow.metadata[0].name, kubernetes_namespace.monitoring.metadata[0].name]
}
```

**Step 5: 验证 Terraform 配置**

```bash
cd infra/terraform/environments/local
terraform init
terraform validate
```

Expected: `Success! The configuration is valid.`

**Step 6: Commit**

```bash
git add infra/terraform/
git commit -m "infra: add terraform base configuration for local kind cluster"
```

---

## Task 2: 部署 Redis Cluster

**Files:**
- Create: `infra/helm/xianyuflow-infra/Chart.yaml`
- Create: `infra/helm/xianyuflow-infra/values-redis.yaml`
- Create: `infra/helm/xianyuflow-infra/templates/redis.yaml`
- Modify: `infra/terraform/environments/local/main.tf`

**Step 1: 创建 Helm Chart 元数据**

```yaml
# infra/helm/xianyuflow-infra/Chart.yaml
apiVersion: v2
name: xianyuflow-infra
description: XianyuFlow infrastructure components
type: application
version: 0.1.0
appVersion: "1.0.0"
dependencies:
  - name: redis-cluster
    version: "9.0.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
  - name: postgresql
    version: "13.2.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
  - name: kafka
    version: "26.4.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: kafka.enabled
```

**Step 2: 创建 Redis 配置文件**

```yaml
# infra/helm/xianyuflow-infra/values-redis.yaml
redis-cluster:
  enabled: true
  cluster:
    nodes: 6
    replicas: 1
  password: "xianyu2024"
  persistence:
    enabled: true
    size: 10Gi
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
      namespace: monitoring
```

**Step 3: 在 Terraform 中添加 Redis 部署**

```hcl
# 添加到 infra/terraform/environments/local/main.tf

# 部署 Redis Cluster
resource "helm_release" "redis" {
  name       = "redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis-cluster"
  version    = "9.0.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../../helm/xianyuflow-infra/values-redis.yaml")
  ]

  set_sensitive {
    name  = "password"
    value = var.redis_password
  }

  depends_on = [kubernetes_namespace.xianyuflow]
}
```

**Step 4: 验证配置**

```bash
cd infra/terraform/environments/local
terraform plan
```

Expected: 显示将要创建的 Redis Cluster 资源

**Step 5: Commit**

```bash
git add infra/helm/ infra/terraform/
git commit -m "infra: add redis cluster helm configuration"
```

---

## Task 3: 部署 PostgreSQL

**Files:**
- Create: `infra/helm/xianyuflow-infra/values-postgres.yaml`
- Modify: `infra/terraform/environments/local/main.tf`

**Step 1: 创建 PostgreSQL 配置文件**

```yaml
# infra/helm/xianyuflow-infra/values-postgres.yaml
postgresql:
  enabled: true
  auth:
    username: xianyu
    password: "xianyu2024"
    database: xianyuflow
    postgresPassword: "admin2024"

  architecture: replication

  primary:
    persistence:
      enabled: true
      size: 20Gi
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "2Gi"
        cpu: "1000m"

  readReplicas:
    replicaCount: 1
    persistence:
      enabled: true
      size: 20Gi
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"

  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
      namespace: monitoring
```

**Step 2: 添加 PostgreSQL 到 Terraform**

```hcl
# 添加到 infra/terraform/environments/local/main.tf

# 部署 PostgreSQL
resource "helm_release" "postgresql" {
  name       = "postgresql"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  version    = "13.2.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../../helm/xianyuflow-infra/values-postgres.yaml")
  ]

  set_sensitive {
    name  = "auth.postgresPassword"
    value = var.postgres_password
  }

  depends_on = [kubernetes_namespace.xianyuflow]
}
```

**Step 3: Commit**

```bash
git add infra/
git commit -m "infra: add postgresql configuration with replication"
```

---

## Task 4: 部署 Kafka

**Files:**
- Create: `infra/helm/xianyuflow-infra/values-kafka.yaml`
- Modify: `infra/terraform/environments/local/main.tf`

**Step 1: 创建 Kafka 配置文件**

```yaml
# infra/helm/xianyuflow-infra/values-kafka.yaml
kafka:
  enabled: true

  replicaCount: 3

  persistence:
    enabled: true
    size: 20Gi

  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

  zookeeper:
    enabled: true
    replicaCount: 3
    persistence:
      enabled: true
      size: 10Gi

  # 预创建主题
  provisioning:
    enabled: true
    topics:
      - name: orders.paid
        partitions: 3
        replicationFactor: 2
      - name: messages.received
        partitions: 6
        replicationFactor: 2
      - name: quotes.calculated
        partitions: 3
        replicationFactor: 2
      - name: listings.published
        partitions: 2
        replicationFactor: 2
      - name: cookies.expired
        partitions: 2
        replicationFactor: 2

  metrics:
    kafka:
      enabled: true
    jmx:
      enabled: true
    serviceMonitor:
      enabled: true
      namespace: monitoring
```

**Step 2: 添加 Kafka 到 Terraform**

```hcl
# 添加到 infra/terraform/environments/local/main.tf

# 部署 Kafka
resource "helm_release" "kafka" {
  name       = "kafka"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "kafka"
  version    = "26.4.0"
  namespace  = kubernetes_namespace.xianyuflow.metadata[0].name

  values = [
    file("${path.module}/../../helm/xianyuflow-infra/values-kafka.yaml")
  ]

  depends_on = [kubernetes_namespace.xianyuflow]
}
```

**Step 3: Commit**

```bash
git add infra/
git commit -m "infra: add kafka with pre-configured topics"
```

---

## Task 5: 部署监控栈 (Prometheus + Grafana)

**Files:**
- Create: `infra/helm/xianyuflow-infra/values-monitoring.yaml`
- Modify: `infra/terraform/environments/local/main.tf`

**Step 1: 创建监控配置文件**

```yaml
# infra/helm/xianyuflow-infra/values-monitoring.yaml
prometheus:
  server:
    enabled: true
    persistentVolume:
      enabled: true
      size: 20Gi
    resources:
      requests:
        memory: "2Gi"
        cpu: "500m"
      limits:
        memory: "4Gi"
        cpu: "1000m"

  alertmanager:
    enabled: true
    persistence:
      enabled: true
      size: 10Gi

  nodeExporter:
    enabled: true

  pushgateway:
    enabled: true

grafana:
  enabled: true
  adminPassword: "xianyu2024"
  persistence:
    enabled: true
    size: 10Gi
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"
  datasources:
    datasources.yaml:
      apiVersion: 1
      datasources:
        - name: Prometheus
          type: prometheus
          url: http://prometheus-server.monitoring.svc.cluster.local
          access: proxy
          isDefault: true
        - name: Jaeger
          type: jaeger
          url: http://jaeger-query.monitoring.svc.cluster.local:16686
          access: proxy
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: 'default'
          orgId: 1
          folder: ''
          type: file
          disableDeletion: false
          editable: true
          options:
            path: /var/lib/grafana/dashboards/default
  dashboards:
    default:
      xianyuflow-overview:
        url: https://raw.githubusercontent.com/grafana/grafana/main/dashboards/json/xianyuflow.json
```

**Step 2: 添加监控到 Terraform**

```hcl
# 添加到 infra/terraform/environments/local/main.tf

# 添加 Prometheus Helm 仓库
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "55.0.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    file("${path.module}/../../helm/xianyuflow-infra/values-monitoring.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}
```

**Step 3: Commit**

```bash
git add infra/
git commit -m "infra: add prometheus and grafana monitoring stack"
```

---

## Task 6: 部署 Jaeger (分布式追踪)

**Files:**
- Create: `infra/helm/xianyuflow-infra/values-jaeger.yaml`
- Modify: `infra/terraform/environments/local/main.tf`

**Step 1: 创建 Jaeger 配置文件**

```yaml
# infra/helm/xianyuflow-infra/values-jaeger.yaml
jaeger:
  provisionDataStore:
    cassandra: false
    elasticsearch: false
    kafka: false

  storage:
    type: memory

  allInOne:
    enabled: true
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"

  agent:
    enabled: false

  collector:
    enabled: false

  query:
    enabled: false

  ingress:
    enabled: true
    hosts:
      - jaeger.local
```

**Step 2: 添加 Jaeger 到 Terraform**

```hcl
# 添加到 infra/terraform/environments/local/main.tf

# 部署 Jaeger
resource "helm_release" "jaeger" {
  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  version    = "0.73.0"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name

  values = [
    file("${path.module}/../../helm/xianyuflow-infra/values-jaeger.yaml")
  ]

  depends_on = [kubernetes_namespace.monitoring]
}
```

**Step 3: Commit**

```bash
git add infra/
git commit -m "infra: add jaeger distributed tracing"
```

---

## Task 7: 创建一键启动脚本

**Files:**
- Create: `infra/scripts/setup-local.sh`
- Create: `infra/scripts/teardown-local.sh`

**Step 1: 创建启动脚本**

```bash
#!/bin/bash
# infra/scripts/setup-local.sh

set -e

echo "🚀 Setting up XianyuFlow local infrastructure..."

# 检查依赖
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform is required but not installed."; exit 1; }
command -v kind >/dev/null 2>&1 || { echo "❌ Kind is required but not installed."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed."; exit 1; }
command -v helm >/dev/null 2>&1 || { echo "❌ Helm is required but not installed."; exit 1; }

cd "$(dirname "$0")/../terraform/environments/local"

echo "📦 Initializing Terraform..."
terraform init

echo "🏗️  Creating Kind cluster..."
terraform apply -auto-approve

echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=redis-cluster -n xianyuflow --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n xianyuflow --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kafka -n xianyuflow --timeout=300s

echo ""
echo "✅ Infrastructure is ready!"
echo ""
echo "Services:"
echo "  Redis:      kubectl port-forward svc/redis-redis-cluster 6379:6379 -n xianyuflow"
echo "  PostgreSQL: kubectl port-forward svc/postgresql 5432:5432 -n xianyuflow"
echo "  Kafka:      kubectl port-forward svc/kafka 9092:9092 -n xianyuflow"
echo "  Grafana:    kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring"
echo "  Jaeger:     kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring"
```

**Step 2: 创建销毁脚本**

```bash
#!/bin/bash
# infra/scripts/teardown-local.sh

set -e

echo "🛑 Tearing down XianyuFlow local infrastructure..."

cd "$(dirname "$0")/../terraform/environments/local"

echo "🗑️  Destroying Terraform resources..."
terraform destroy -auto-approve

echo "✅ Infrastructure destroyed successfully!"
```

**Step 3: 添加执行权限并测试**

```bash
chmod +x infra/scripts/*.sh
```

**Step 4: Commit**

```bash
git add infra/scripts/
git commit -m "infra: add setup and teardown scripts for local environment"
```

---

## Task 8: 创建文档和验证

**Files:**
- Create: `infra/README.md`
- Create: `docs/DEPLOYMENT_INFRA.md`

**Step 1: 创建基础设施 README**

```markdown
# XianyuFlow Infrastructure

本地开发环境基础设施。

## 快速开始

```bash
# 启动所有服务
./infra/scripts/setup-local.sh

# 验证服务状态
kubectl get pods -n xianyuflow
kubectl get pods -n monitoring

# 访问 Grafana (默认密码: xianyu2024)
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# 打开 http://localhost:3000
```

## 组件说明

| 组件 | 版本 | 用途 | 访问方式 |
|------|------|------|----------|
| Redis Cluster | 7.x | 会话存储、缓存 | localhost:6379 |
| PostgreSQL | 16.x | 主数据库 | localhost:5432 |
| Kafka | 3.6.x | 事件流 | localhost:9092 |
| Prometheus | 2.x | 指标收集 | 通过 Grafana |
| Grafana | 10.x | 可视化 | localhost:3000 |
| Jaeger | 1.50 | 分布式追踪 | localhost:16686 |

## 目录结构

- `terraform/` - 基础设施即代码
- `helm/` - Helm Charts
- `scripts/` - 运维脚本
```

**Step 2: 创建部署文档**

```markdown
# 基础设施部署指南

## 本地开发环境

### 前置要求

- Docker Desktop (with Kubernetes enabled) 或 Docker + Kind
- Terraform >= 1.5.0
- kubectl
- Helm >= 3.0

### 部署步骤

1. 克隆仓库
2. 运行启动脚本
3. 验证服务
4. 配置应用连接

### 生产环境

生产环境使用 EKS，详见 `infra/terraform/environments/production/`。
```

**Step 3: Commit**

```bash
git add infra/README.md docs/
git commit -m "docs: add infrastructure deployment documentation"
```

---

## 验证清单

Phase 1 完成后，应验证以下功能：

- [ ] Kind 集群成功创建（`kind get clusters`）
- [ ] Redis Cluster 6 节点正常运行（`kubectl get pods -n xianyuflow -l app.kubernetes.io/name=redis-cluster`）
- [ ] PostgreSQL 主从复制正常（`kubectl get pods -n xianyuflow -l app.kubernetes.io/name=postgresql`）
- [ ] Kafka 3 节点 + 预创建主题（`kubectl exec -it kafka-0 -n xianyuflow -- kafka-topics.sh --list --bootstrap-server localhost:9092`）
- [ ] Prometheus 采集指标正常（Grafana Explore 页面）
- [ ] Jaeger UI 可访问（`kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring`）

---

## 下一步

Phase 1 完成后，进入 Phase 2：服务拆分。

参考设计文档：`docs/superpowers/specs/2026-03-27-xianyuflow-v10-architecture-design.md`

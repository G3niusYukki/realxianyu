# 基础设施部署指南

> 本文档只覆盖 `infra/` 目录下的本地基础设施资产，不代表“完整应用也会随之一起部署”。

## 当前适用范围

当前仓库中的 infra 资产主要用于：

- 本地 Kind 集群
- Terraform 环境初始化
- Redis / PostgreSQL / Kafka / 监控等基础设施实验

不应把它理解成：

- 当前 `main` 已有完整 Helm 应用交付
- 运行 `setup-local.sh` 后就能得到完整前端 + API 工作台

## 已存在的关键路径

- `infra/scripts/setup-local.sh`
- `infra/terraform/environments/local/main.tf`
- `infra/helm/`

## 本地基础设施启动

### 前置依赖

- Docker
- Kind
- kubectl
- Terraform
- Helm

### 启动

```bash
./infra/scripts/setup-local.sh
```

脚本会负责本地基础设施的初始化与部署。

## 验证

```bash
kubectl get pods -A
```

根据你选择启用的组件，通常应重点检查：

- PostgreSQL
- Redis
- Kafka
- monitoring 相关组件

## 常见访问方式

### Grafana

```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

### PostgreSQL

```bash
kubectl port-forward svc/postgresql 5432:5432 -n xianyuflow
```

### Redis

```bash
kubectl port-forward svc/redis-redis-cluster 6379:6379 -n xianyuflow
```

### Kafka

```bash
kubectl port-forward svc/kafka 9092:9092 -n xianyuflow
```

## 与应用部署的关系

当前仓库真实情况：

- Dashboard UI/API 主链路仍靠 `src.dashboard_server`
- `gateway-service` 可单独运行
- 不存在 `services/helm/xianyuflow`

所以常见组合是：

1. 用 infra 启动本地依赖栈
2. 再单独启动 `src.dashboard_server`
3. 需要时再单独启动 `gateway-service`

## 清理

```bash
./infra/scripts/teardown-local.sh
```

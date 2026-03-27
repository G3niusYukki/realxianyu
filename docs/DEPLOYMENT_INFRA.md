# 基础设施部署指南

本文档详细说明 XianyuFlow v10 基础设施的部署流程。

## 系统要求

### 本地开发环境

- **Docker Desktop** 20.10+ (macOS/Windows) 或 Docker Engine + Docker Compose (Linux)
- **Kind** 0.20+ ([安装指南](https://kind.sigs.k8s.io/docs/user/quick-start/))
- **Terraform** 1.5+ ([安装指南](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli))
- **kubectl** 1.28+ ([安装指南](https://kubernetes.io/docs/tasks/tools/))
- **Helm** 3.13+ ([安装指南](https://helm.sh/docs/intro/install/))

### 资源需求

建议预留以下资源：

- **CPU**: 8 核心
- **内存**: 16 GB
- **磁盘**: 50 GB 可用空间

## 部署步骤

### 1. 克隆仓库

```bash
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu
```

### 2. 启动基础设施

```bash
./infra/scripts/setup-local.sh
```

该脚本将：
1. 检查所有依赖项
2. 初始化 Terraform
3. 创建 Kind 集群
4. 部署所有基础设施组件
5. 等待服务就绪

整个过程大约需要 5-10 分钟，取决于网络速度和机器性能。

### 3. 验证部署

```bash
# 查看所有 Pod
kubectl get pods -A

# 所有 Pod 应该处于 Running 状态
NAMESPACE     NAME                                               READY   STATUS
monitoring    jaeger-xxx                                         1/1     Running
monitoring    prometheus-grafana-xxx                             3/3     Running
monitoring    prometheus-kube-prometheus-prometheus-0            2/2     Running
xianyuflow    kafka-0                                            1/1     Running
xianyuflow    kafka-1                                            1/1     Running
xianyuflow    kafka-2                                            1/1     Running
xianyuflow    postgresql-postgresql-0                            2/2     Running
xianyuflow    redis-redis-cluster-0                              2/2     Running
xianyuflow    redis-redis-cluster-1                              2/2     Running
xianyuflow    redis-redis-cluster-2                              2/2     Running
```

### 4. 访问服务

#### Grafana

```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

访问 http://localhost:3000
- 用户名: `admin`
- 密码: `xianyu2024`

#### Jaeger UI

```bash
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring
```

访问 http://localhost:16686

#### PostgreSQL

```bash
kubectl port-forward svc/postgresql 5432:5432 -n xianyuflow
```

连接参数：
- Host: `localhost`
- Port: `5432`
- Database: `xianyuflow`
- Username: `xianyu`
- Password: `xianyu2024`

#### Redis

```bash
kubectl port-forward svc/redis-redis-cluster 6379:6379 -n xianyuflow
```

连接参数：
- Host: `localhost`
- Port: `6379`
- Password: `xianyu2024`

#### Kafka

```bash
kubectl port-forward svc/kafka 9092:9092 -n xianyuflow
```

## 配置说明

### 数据库初始化

PostgreSQL 首次启动时会自动创建数据库和用户。如需手动执行初始化脚本：

```bash
# 进入 PostgreSQL Pod
kubectl exec -it postgresql-postgresql-0 -n xianyuflow -- psql -U xianyu -d xianyuflow

# 执行 SQL
\i /path/to/init.sql
```

### Kafka 主题管理

```bash
# 列出所有主题
kubectl exec -it kafka-0 -n xianyuflow -- kafka-topics.sh --list --bootstrap-server localhost:9092

# 创建新主题
kubectl exec -it kafka-0 -n xianyuflow -- kafka-topics.sh --create \
  --topic my-topic \
  --partitions 3 \
  --replication-factor 2 \
  --bootstrap-server localhost:9092

# 查看主题详情
kubectl exec -it kafka-0 -n xianyuflow -- kafka-topics.sh --describe \
  --topic orders.paid \
  --bootstrap-server localhost:9092
```

## 监控配置

### Prometheus 抓取配置

默认已配置以下抓取目标：

- Kubernetes API Server
- Node Exporter
- Kubelet
- 所有部署的服务（通过 ServiceMonitor）

### 添加自定义仪表盘

```bash
# 将 JSON 格式的仪表盘配置保存到 ConfigMap
kubectl create configmap xianyuflow-dashboards \
  --from-file=dashboard.json \
  -n monitoring

# 重启 Grafana
kubectl rollout restart deployment/prometheus-grafana -n monitoring
```

## 故障排查

### 常见问题

**Q: Pod 一直处于 Pending 状态**

A: 检查资源是否充足：
```bash
kubectl describe node
```

如果磁盘压力或内存压力过高，Kind 集群可能无法调度 Pod。

**Q: Terraform apply 失败**

A: 检查 Helm 仓库是否可访问：
```bash
helm repo list
helm search repo bitnami/redis-cluster
```

如果无法访问，可能需要配置代理或镜像源。

**Q: Kafka 消费延迟高**

A: 检查分区数量和消费者组配置：
```bash
kubectl exec -it kafka-0 -n xianyuflow -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group my-group
```

## 安全注意事项

⚠️ **本地开发环境使用默认密码，请勿用于生产！**

生产环境应该：
1. 使用强密码（32+ 随机字符）
2. 启用 TLS 加密
3. 配置网络隔离
4. 使用 Vault 或 KMS 管理密钥

## 清理资源

```bash
# 销毁所有基础设施
./infra/scripts/teardown-local.sh

# 如需彻底清理（包括 Kind 集群）
kind delete cluster --name xianyuflow-local
```

---

更多详情请参考 [架构设计文档](../superpowers/specs/2026-03-27-xianyuflow-v10-architecture-design.md)

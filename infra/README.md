# XianyuFlow Infrastructure

XianyuFlow v10 基础设施配置 - 本地开发环境。

## 快速开始

```bash
# 启动所有基础设施服务
./infra/scripts/setup-local.sh

# 查看服务状态
kubectl get pods -n xianyuflow
kubectl get pods -n monitoring

# 访问 Grafana (默认密码: xianyu2024)
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# 打开 http://localhost:3000

# 访问 Jaeger UI
kubectl port-forward svc/jaeger-query 16686:16686 -n monitoring
# 打开 http://localhost:16686

# 销毁环境
./infra/scripts/teardown-local.sh
```

## 组件说明

| 组件 | 版本 | 用途 | 访问方式 |
|------|------|------|----------|
| Redis Cluster | 7.x | 会话存储、缓存 | `localhost:6379` (port-forward) |
| PostgreSQL | 16.x | 主数据库 | `localhost:5432` (port-forward) |
| Kafka | 3.6.x | 事件流 | `localhost:9092` (port-forward) |
| Prometheus | 2.x | 指标收集 | Via Grafana |
| Grafana | 10.x | 可视化 | `localhost:3000` |
| Jaeger | 1.50 | 分布式追踪 | `localhost:16686` |

## 目录结构

```
infra/
├── terraform/          # 基础设施即代码 (Terraform)
│   └── environments/
│       └── local/      # 本地开发环境
├── helm/               # Helm Charts
│   └── xianyuflow-infra/
└── scripts/            # 运维脚本
```

## 环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
# 数据库密码
DB_PASSWORD=xianyu2024

# Redis 密码
REDIS_PASSWORD=xianyu2024

# 闲鱼 API 凭证
XIANYU_APP_KEY=your_app_key
XIANYU_APP_SECRET=your_app_secret
```

## Kafka 主题

预创建的主题：

| 主题 | 分区数 | 复制因子 | 用途 |
|------|--------|----------|------|
| `orders.paid` | 3 | 2 | 订单支付事件 |
| `messages.received` | 6 | 2 | 新消息事件 |
| `quotes.calculated` | 3 | 2 | 报价完成事件 |
| `listings.published` | 2 | 2 | 商品上架事件 |
| `cookies.expired` | 2 | 2 | Cookie 过期事件 |

## 故障排查

### Pod 启动失败

```bash
# 查看 Pod 事件
kubectl describe pod <pod-name> -n <namespace>

# 查看日志
kubectl logs <pod-name> -n <namespace>

# 查看所有资源
kubectl get all -n xianyuflow
```

### Terraform 状态问题

```bash
# 重新初始化
cd infra/terraform/environments/local
terraform init -reconfigure

# 查看状态
terraform state list

# 手动删除状态（危险！）
rm terraform.tfstate terraform.tfstate.backup
```

### Kind 集群问题

```bash
# 列出集群
kind get clusters

# 删除集群
kind delete cluster --name xianyuflow-local

# 重新创建
./infra/scripts/setup-local.sh
```

## 开发指南

### 添加新的 Helm Chart

1. 更新 `helm/xianyuflow-infra/Chart.yaml` 添加依赖
2. 创建 `values-<name>.yaml` 配置文件
3. 更新 `terraform/environments/local/main.tf` 添加 `helm_release` 资源
4. 运行 `terraform apply`

### 修改配置

```bash
# 编辑 values 文件
vim infra/helm/xianyuflow-infra/values-redis.yaml

# 应用更改
cd infra/terraform/environments/local
terraform apply
```

## 生产环境

生产环境使用 AWS EKS，配置在 `terraform/environments/production/`。

主要区别：
- 使用 RDS 替代本地 PostgreSQL
- 使用 ElastiCache 替代本地 Redis
- 使用 MSK 替代本地 Kafka
- 使用托管 Prometheus/Grafana

---

*XianyuFlow v10 Infrastructure | 2026*

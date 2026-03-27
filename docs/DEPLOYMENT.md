# 部署指南

> XianyuFlow | 闲流 (realxianyu) v10.0.0 部署完整方案

---

## 部署方式概览

| 方式 | 适用场景 | 难度 | 依赖 |
|------|---------|------|------|
| **Kind 本地集群** | 开发/测试 | ⭐⭐ | Docker + Kind + kubectl + Helm |
| **AWS EKS 生产** | 生产环境 | ⭐⭐⭐ | AWS 账号 + Terraform |
| **本地 Python** | 单机运行 | ⭐ | Python 3.12+ |

---

## 前置要求

### 必备条件

| 项目 | 说明 | 获取方式 |
|------|------|---------|
| **闲鱼 Cookie** | 登录凭证 | 浏览器 F12 复制，或启动后在管理面板自动获取 |
| **AI API Key** | 自动回复需要 | 推荐 [DeepSeek](https://platform.deepseek.com)（价格低、效果好） |
| **闲管家凭证** | 订单/发货/改价 | [闲管家开放平台](https://open.goofish.pro) 注册应用获取 |

### 必备软件

| 软件 | 版本 | 说明 |
|------|------|------|
| Docker | 24.0+ | 容器运行时 |
| kubectl | 1.28+ | K8s CLI |
| Helm | 3.12+ | K8s 包管理器 |
| Terraform | 1.6+ | 基础设施即代码 |

---

## 方式一：Kind 本地集群（推荐开发）

### 1. 安装依赖

```bash
# macOS
brew install kind kubectl helm docker

# Ubuntu/Debian
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl -fsSL https://get.docker.com | sh
```

### 2. 创建 Kind 集群

```bash
kind create cluster --name xianyuflow --wait 5m

# 验证
kubectl cluster-info
```

### 3. 部署基础设施 (Terraform)

```bash
cd infra/terraform/environments/local

terraform init
terraform validate
terraform plan
terraform apply

# 等待所有 Pod 就绪
kubectl wait --for=condition=ready pod -l app=redis -n xianyuflow --timeout=300s
kubectl wait --for=condition=ready pod -l app=postgresql -n xianyuflow --timeout=300s
```

### 4. 构建并推送镜像

```bash
# 设置镜像仓库（使用 kind 内置 registry）
export REGISTRY=localhost:5000

# 构建所有服务镜像
for service in gateway quote ai message order scheduler; do
  docker build -t ${REGISTRY}/xianyuflow/${service}:v10.0.0 \
    -f services/${service}/Dockerfile services/
done

# 推送镜像
for service in gateway quote ai message order scheduler; do
  docker push ${REGISTRY}/xianyuflow/${service}:v10.0.0
done
```

### 5. 部署应用 (Helm)

```bash
cd ../../..

helm install xianyuflow ./services/helm/xianyuflow \
  --namespace xianyuflow \
  --create-namespace \
  --set global.image.tag=v10.0.0 \
  --set global.image.registry=localhost:5000

# 验证部署
kubectl get pods -n xianyuflow
kubectl get svc -n xianyuflow
```

### 6. 配置服务

```bash
# 创建配置 Secret
kubectl create secret generic xianyuflow-config \
  --from-literal=XIANYU_COOKIE="$XIANYU_COOKIE_1" \
  --from-literal=DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY" \
  --from-literal=XGJ_APP_KEY="$XGJ_APP_KEY" \
  --from-literal=XGJ_APP_SECRET="$XGJ_APP_SECRET" \
  -n xianyuflow

# 重启服务加载配置
kubectl rollout restart deployment -n xianyuflow
```

### 7. 访问服务

```bash
# 端口转发（开发用）
kubectl port-forward svc/gateway-service 8000:8000 -n xianyuflow

# 或使用 Ingress
# 访问 http://api.xianyuflow.local
```

---

## 方式二：AWS EKS 生产部署

### 1. 配置 AWS 环境

```bash
# 安装 AWS CLI 和 eksctl
brew install awscli eksctl

# 配置凭证
aws configure

# 设置默认区域
export AWS_DEFAULT_REGION=ap-east-1
```

### 2. 创建 EKS 集群 (Terraform)

```bash
cd infra/terraform/environments/prod

terraform init
terraform plan -var="cluster_name=xianyuflow-prod"
terraform apply -var="cluster_name=xianyuflow-prod"
```

### 3. 配置 kubectl

```bash
aws eks update-kubeconfig \
  --name xianyuflow-prod \
  --region ap-east-1 \
  --kubeconfig ~/.kube/config-xianyuflow

export KUBECONFIG=~/.kube/config-xianyuflow
```

### 4. 部署基础设施组件

```bash
# 部署 Ingress Controller
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.replicaCount=2 \
  --set controller.nodeSelector.eks.amazonaws.com/nodegroup=system

# 部署 Metrics Server
helm install metrics-server metrics-server/metrics-server \
  --namespace kube-system
```

### 5. 部署应用

```bash
cd ../../..

# 创建生产配置
cp services/helm/xianyuflow/values.prod.example.yaml values.prod.yaml
# 编辑 values.prod.yaml 配置生产参数

# 部署
helm install xianyuflow ./services/helm/xianyuflow \
  --namespace xianyuflow \
  --create-namespace \
  --values values.prod.yaml \
  --set global.environment=production

# 启用 HPA 自动伸缩
kubectl autoscale deployment gateway-service \
  --namespace xianyuflow \
  --min=2 --max=10 --cpu-percent=70
```

### 6. 配置域名和证书

```bash
# 创建 Ingress
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: xianyuflow-ingress
  namespace: xianyuflow
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.xianyuflow.com
    secretName: xianyuflow-tls
  rules:
  - host: api.xianyuflow.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gateway-service
            port:
              number: 8000
EOF
```

---

## 方式三：本地 Python 开发

适用于不需要 Kubernetes 的场景：

```bash
# 1. 启动依赖
docker compose -f docker-compose.dev.yml up -d

# 2. 安装依赖
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 填入 XIANYU_COOKIE、DEEPSEEK_API_KEY 等

# 4. 启动服务
python -m services.gateway_service.app
```

---

## 灰度发布

### 使用 Canary 部署

```bash
# 部署 10% canary 流量
kubectl apply -f k8s/canary-deployment.yaml

# 调整流量权重
kubectl annotate ingress message-service-ingress \
  nginx.ingress.kubernetes.io/canary-weight="25" \
  -n xianyuflow

# 监控指标
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# 访问 http://localhost:3000 查看 Grafana
```

### 发布检查清单

- [ ] Error rate < 0.1%
- [ ] P99 latency < 500ms
- [ ] CPU usage < 80%
- [ ] Memory usage < 80%
- [ ] 业务指标正常

---

## 应急回滚

### 应用回滚

```bash
# 回滚单个服务
./scripts/rollback.sh message-service --force

# 回滚所有服务
./scripts/rollback.sh all --force
```

### 数据库回滚

```bash
# 切换回 SQLite
kubectl set env deployment/gateway-service \
  READ_MODE=sqlite_only -n xianyuflow

kubectl set env deployment/gateway-service \
  WRITE_MODE=sqlite_only -n xianyuflow

kubectl rollout restart deployment -n xianyuflow
```

---

## 数据备份

### PostgreSQL 备份

```bash
# 创建备份 Job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: xianyuflow
spec:
  schedule: "0 2 * * *"
  successfulJobsHistoryLimit: 7
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgresql -U xianyu xianyuflow > /backups/backup-$(date +%Y%m%d).sql
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
          restartPolicy: OnFailure
EOF
```

### SQLite 迁移后备份

```bash
# 迁移前备份
kubectl exec -n xianyuflow deploy/gateway-service -- \
  sh -c 'cp /data/orders.db /data/orders.db.backup'
```

---

## 故障排查

### 检查服务状态

```bash
# 查看所有 Pod
kubectl get pods -n xianyuflow

# 查看服务日志
kubectl logs -f deployment/gateway-service -n xianyuflow

# 查看资源使用
kubectl top pods -n xianyuflow
```

### 常见问题

| 问题 | 解决方案 |
|------|---------|
| Pod 无法启动 | `kubectl describe pod <name>` 查看事件 |
| 镜像拉取失败 | 检查镜像仓库配置和 Secret |
| 无法连接数据库 | 检查 PostgreSQL Service 和 Secret |
| Ingress 不工作 | 检查 DNS 解析和证书配置 |

### 诊断工具

```bash
# 完整诊断
kubectl debug -it node/xxx --image=busybox

# 进入 Pod 调试
kubectl exec -it deploy/gateway-service -n xianyuflow -- /bin/sh
```

---

## 更新升级

### 滚动更新

```bash
# 更新镜像版本
helm upgrade xianyuflow ./services/helm/xianyuflow \
  --set global.image.tag=v10.1.0 \
  -n xianyuflow

# 验证更新
kubectl rollout status deployment -n xianyuflow
```

### 数据迁移

```bash
# 运行迁移脚本
kubectl exec -it deploy/gateway-service -n xianyuflow -- \
  python scripts/migrate_data.py --validate
```

---

## 监控和告警

### Prometheus + Grafana

```bash
# 访问 Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# 默认账号: admin/prom-operator
```

### 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| `http_requests_total` | 请求总数 | error_rate > 1% |
| `http_request_duration_seconds` | 请求延迟 | P99 > 500ms |
| `db_connections_active` | 活跃连接 | > 80% 最大值 |
| `canary_error_rate` | Canary 错误率 | > 5% |

---

## 获取帮助

- [README.md](../README.md) — 项目概览
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) — 架构设计
- [docs/MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) — 迁移指南
- [GitHub Issues](https://github.com/G3niusYukki/realxianyu/issues) — 问题反馈

# XianyuFlow | 闲流

[![CI](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml/badge.svg)](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-10.0.0-green.svg)](./CHANGELOG.md)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-326ce5.svg)](https://kubernetes.io/)
[![Microservices](https://img.shields.io/badge/architecture-microservices-ff6b6b.svg)](./docs/ARCHITECTURE.md)

> **XianyuFlow v10.0.0** — 云原生微服务架构升级
>
> 本项目已完成从单体应用到云原生微服务平台的深度重构，基于 Kubernetes 实现弹性伸缩、灰度发布和零停机迁移。

---

## 📚 文档导航

| 文档 | 说明 | 目标读者 |
|------|------|----------|
| [QUICKSTART.md](./QUICKSTART.md) | 5分钟快速启动 | 新用户 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构设计 | 开发者 |
| [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) | 部署指南（K8s/本地） | 运维人员 |
| [docs/MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md) | v9→v10迁移指南 | 现有用户 |
| [docs/API.md](./docs/API.md) | HTTP API 文档 | 前后端开发者 |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | 贡献指南 | 贡献者 |

---

## 🚀 核心特性

| 特性 | 说明 |
|------|------|
| **微服务架构** | 6个独立服务：Gateway、Quote、AI、Message、Order、Scheduler |
| **Kubernetes 原生** | Kind/EKS 部署，Helm Charts，HPA 自动伸缩 |
| **4级 AI 上下文** | Request → Intent → Session → Profile 智能上下文管理 |
| **多级缓存** | L1 (内存 LRU) + L2 (Redis) 双重缓存加速 |
| **零停机迁移** | 双写模式 SQLite → PostgreSQL 平滑迁移 |
| **灰度发布** | NGINX Canary 流量控制，渐进式发布 |
| **全链路可观测** | Prometheus + Grafana + Jaeger 监控追踪 |

---

## 🏗 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Cluster                            │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Gateway   │  │   Quote     │  │     AI      │  │   Message   │  │
│  │  Service    │  │  Service    │  │  Service    │  │  Service    │  │
│  │  :8000      │  │  :8001      │  │  :8002      │  │  :8003      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │                 │                 │                 │         │
│         └─────────────────┼─────────────────┼─────────────────┘         │
│                           │                 │                          │
│                    ┌──────▼─────────────────▼──────┐                   │
│                    │        Kafka Event Bus        │                   │
│                    └───────────────────────────────┘                   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Order     │  │  Scheduler  │  │    Redis    │  │ PostgreSQL  │  │
│  │  Service    │  │  Service    │  │  Cluster    │  │   Master    │  │
│  │  :8004      │  │  :8005      │  │             │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 服务说明

| 服务 | 端口 | 功能 |
|------|------|------|
| **gateway-service** | 8000 | API 网关，限流，路由分发 |
| **quote-service** | 8001 | 物流报价引擎，多级缓存 |
| **ai-service** | 8002 | 4级上下文管理，LLM 调用 |
| **message-service** | 8003 | WebSocket 连接池，消息处理 |
| **order-service** | 8004 | 订单履约，虚拟商品核销 |
| **scheduler-service** | 8005 | 分布式任务调度 |

---

## 💻 快速部署

### 方式一：本地 Kind 集群（推荐开发）

```bash
# 1. 安装依赖
brew install kind kubectl helm docker

# 2. 创建集群
kind create cluster --name xianyuflow

# 3. 部署基础设施
cd infra/terraform/environments/local
terraform init && terraform apply

# 4. 部署应用
cd ../../..
helm install xianyuflow ./services/helm/xianyuflow \
  --set global.image.tag=v10.0.0

# 5. 验证部署
kubectl get pods -n xianyuflow
```

### 方式二：本地 Python 开发

```bash
# 1. 克隆并进入目录
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu

# 2. 启动依赖服务
docker compose up -d redis postgres

# 3. 安装依赖
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 填入 XIANYU_COOKIE_1、DEEPSEEK_API_KEY 等

# 5. 启动服务
python -m services.gateway_service.app
```

### 方式三：AWS EKS 生产部署

```bash
# 1. 配置 AWS 凭证
aws configure

# 2. 创建 EKS 集群
cd infra/terraform/environments/prod
terraform init && terraform apply

# 3. 配置 kubectl
aws eks update-kubeconfig --name xianyuflow-prod

# 4. 部署应用
helm install xianyuflow ./services/helm/xianyuflow \
  --namespace xianyuflow \
  --set global.environment=production \
  --values values.prod.yaml
```

---

## 🤖 For AI Agents

AI Agent 可通过以下方式自动部署：

```bash
curl -s https://raw.githubusercontent.com/G3niusYukki/realxianyu/main/AGENT_DEPLOYMENT.md
```

或直接告诉 Agent：**"Deploy this project following AGENT_DEPLOYMENT.md"**

---

## 🧪 测试

```bash
# 运行所有服务测试
pytest services/*/tests/ -v

# 运行基础设施测试
pytest tests/integration/ -v

# 代码规范检查
ruff check services/ --extend-ignore I001,E501

# Kubernetes 配置验证
kubectl lint services/k8s/
```

---

## 📂 目录结构

```
realxianyu/
├── services/                    # 微服务代码
│   ├── gateway-service/         # API 网关
│   ├── quote-service/          # 报价服务
│   ├── ai-service/             # AI 服务
│   ├── message-service/        # 消息服务
│   ├── order-service/          # 订单服务
│   ├── scheduler-service/      # 调度服务
│   ├── common/                 # 公共库
│   │   └── xianyuflow_common/ # 配置/缓存/双写
│   └── helm/                   # Helm Charts
├── infra/                      # 基础设施代码
│   ├── terraform/              # Terraform 配置
│   │   └── environments/      # 环境配置
│   │       ├── local/         # Kind 本地
│   │       └── prod/          # AWS EKS
│   └── k8s/                   # K8s 资源配置
├── scripts/                    # 运维脚本
│   ├── migrate_data.py         # 数据迁移
│   └── rollback.sh             # 应急回滚
├── docs/                       # 文档
│   ├── ARCHITECTURE.md        # 架构设计
│   ├── DEPLOYMENT.md          # 部署指南
│   └── MIGRATION_GUIDE.md    # 迁移指南
├── client/                     # React 前端
├── src/                        # (遗留) 单体代码
└── CHANGELOG.md               # 版本变更日志
```

---

## 🔄 从 v9 升级

如需从 v9.x 升级到 v10，请参考 [迁移指南](./docs/MIGRATION_GUIDE.md)。

**主要变更：**
- SQLite 数据库迁移到 PostgreSQL
- 单体应用拆分为 6 个独立服务
- 新增 Kubernetes 部署支持
- 配置管理从 `config.yaml` 迁移到 Pydantic 模型

---

## 📜 许可协议

[MIT License](./LICENSE)

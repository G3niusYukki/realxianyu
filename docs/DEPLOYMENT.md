# 部署指南

> 本文档只描述当前 `main` 已经验证可运行的部署路径，不再把“计划中的完整 v10 K8s 微服务交付”写成既成事实。

## 一、支持的部署方式

| 方式 | 状态 | 说明 |
|------|------|------|
| Dashboard 本地部署 | 已验证 | `src.dashboard_server` 提供 UI + `/api/*` |
| Gateway 本地部署 | 已验证 | `services/gateway-service` 提供 Open Platform 适配 API |
| Infra 本地集群 | 部分可用 | `infra/scripts/setup-local.sh` 可部署基础设施 |
| 完整 Helm 应用部署 | 当前不完整 | `services/helm/xianyuflow` 不存在 |

## 二、推荐本地部署

### 1. 安装依赖

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
```

### 2. 准备配置

```bash
cp .env.example .env
```

至少建议检查这些值：

- `XGJ_APP_KEY` / `XGJ_APP_SECRET`
- `DEEPSEEK_API_KEY` 或其他 AI 配置
- Cookie 相关配置

## 三、启动 Dashboard 主服务

```bash
python -m src.dashboard_server --host 127.0.0.1 --port 8091
```

验证：

```bash
curl -s http://127.0.0.1:8091/healthz
```

访问：

- `http://127.0.0.1:8091/`

说明：

- `8091` 才是浏览器默认打开的 UI 页面
- 如果 `client/dist` 不存在，根路径会提示前端尚未构建

## 四、可选启动 Gateway Service

如果你要单独验证闲管家 Open Platform 适配：

```bash
pip install -e services/common -e services/gateway-service
cd services/gateway-service
../../venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

验证：

```bash
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/health
```

说明：

- `8000` 返回 JSON，不是前端页面
- 浏览器如果打开 `8000`，看到 JSON 代表服务是正常的

## 五、端口说明

| 端口 | 作用 |
|------|------|
| `8091` | Dashboard UI + Dashboard API |
| `8000` | Gateway API |
| `5173` | Vite 开发端口 |

如果需要让局域网或容器外部访问，把 `127.0.0.1` 改成 `0.0.0.0`。

## 六、当前不应照抄的旧命令

以下说法在当前 `main` 中不成立或不完整：

- `docker-compose.dev.yml` 一键拉起整套应用
- `helm install ./services/helm/xianyuflow`
- `services/scheduler-service` 已存在并参与部署
- “完整 v10 微服务已经完全替代 dashboard_server”

## 七、基础设施部署边界

仓库中确实存在：

- `infra/scripts/setup-local.sh`
- `infra/terraform/environments/local`
- `infra/helm`

但这些更准确地对应“基础设施层”而不是“完整应用层”。如果你只想把当前主线跑起来，优先使用本页前两节。

## 八、验证清单

### Dashboard

```bash
curl -s http://127.0.0.1:8091/healthz
```

### Gateway

```bash
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/api/v1/users/authorized
```

### 前端构建

```bash
cd client && npm run build
```

### Python 测试

```bash
./venv/bin/python -m pytest tests/ -q
```

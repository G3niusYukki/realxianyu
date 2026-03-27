# XianyuFlow | 闲流

[![CI](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml/badge.svg)](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

闲鱼运营自动化工具，覆盖消息自动回复、智能报价、订单履约、商品上架、Cookie 管理和运维诊断。

## 当前主线状态

当前 `main` 是混合形态：

- 主入口仍是 Python Dashboard 服务 `src/dashboard_server.py`
- React 前端构建产物由 Dashboard 服务托管
- `services/` 下存在 v10 服务化代码与基础设施资产，但并非“完整 Helm/K8s 一键应用部署”
- `gateway-service` 现在可单独运行，并已对齐闲管家 Open Platform 请求契约

这意味着：

- 浏览器里的管理界面默认看 `8091`
- `8000` 是 API 网关，不是前端页面
- `services/helm/xianyuflow` 当前不存在
- `services/scheduler-service` 当前不存在

## 运行入口

| 用途 | 地址/命令 | 说明 |
|------|-----------|------|
| Dashboard UI | `http://127.0.0.1:8091/` | 主工作台，托管 `client/dist` |
| Dashboard 健康检查 | `http://127.0.0.1:8091/healthz` | Python 主服务健康状态 |
| Gateway API | `http://127.0.0.1:8000/` | Open Platform 适配网关，根路径返回 JSON |
| Gateway Swagger | `http://127.0.0.1:8000/docs` | FastAPI 文档 |
| Vite 开发端口 | `http://127.0.0.1:5173/` | 仅前端开发时使用，不是生产入口 |

## 本地启动

### 1. 安装依赖

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
```

### 2. 配置环境

```bash
cp .env.example .env
```

运行时优先级：

1. `.env`
2. `data/system_config.json`
3. `config/config.yaml`

### 3. 启动 Dashboard 主服务

```bash
python -m src.dashboard_server --host 127.0.0.1 --port 8091
```

打开：

- `http://127.0.0.1:8091/` 看管理界面
- `http://127.0.0.1:8091/healthz` 看健康检查

### 4. 可选：启动 Gateway Service

```bash
pip install -e services/common -e services/gateway-service
cd services/gateway-service
../../venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## 已验证的当前行为

- `src.dashboard_server` 会在 `8091` 提供 UI 和 `/api/*`
- `client/dist` 已存在时，`8091` 根路径返回前端 HTML
- `gateway-service` 会在 `8000` 提供 Open Platform 适配接口
- `gateway-service` 当前已兼容旧 `XGJ_*` 环境变量，并使用 `/api/open/*` + `appid/timestamp/sign`

## 测试与校验

```bash
./venv/bin/python -m pytest tests/ -q
ruff check src/
cd client && npm run build
```

网关相关回归：

```bash
./venv/bin/python -m pytest \
  tests/test_gateway_service_client.py \
  tests/test_gateway_service_app.py \
  tests/test_xianguanjia_open_platform_client.py \
  -q --no-cov
```

## 目录概览

```text
client/                     React/Vite 前端
config/                     YAML 主配置
data/system_config.json     Dashboard UI 覆盖配置
docs/                       开发/部署/架构文档
infra/                      Terraform / Helm / 本地基础设施脚本
services/                   v10 服务化代码（当前为部分落地）
src/                        当前主线 Python 业务与 Dashboard 服务
tests/                      pytest 测试
```

## 文档

- [QUICKSTART.md](./QUICKSTART.md)
- [docs/API.md](./docs/API.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)
- [docs/DEPLOYMENT_INFRA.md](./docs/DEPLOYMENT_INFRA.md)
- [docs/MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md)
- [docs/README.md](./docs/README.md)

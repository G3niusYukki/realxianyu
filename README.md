# XianyuFlow | 闲流

[![CI](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml/badge.svg)](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

闲鱼运营自动化工具，覆盖消息自动回复、智能报价、订单履约、商品上架、Cookie 管理和运维诊断。

**当前版本：v10.0.0**

## 架构概览

v10 采用单体 + 网关的简化架构：

- **Python 单体**（`src/`）：Dashboard 服务、消息处理、报价引擎、订单管理等全部业务逻辑
- **Gateway Service**（`services/gateway-service`）：Open Platform 适配网关，独立 FastAPI 服务
- **React 前端**（`client/`）：Vite + Tailwind 构建的管理界面，由 Dashboard 服务托管

## 运行入口

| 用途 | 地址/命令 | 说明 |
|------|-----------|------|
| Dashboard UI | `http://127.0.0.1:8091/` | 主工作台，托管 `client/dist` |
| Dashboard 健康检查 | `http://127.0.0.1:8091/healthz` | Python 主服务健康状态 |
| Gateway API | `http://127.0.0.1:8000/` | Open Platform 适配网关，根路径返回 JSON |
| Gateway Swagger | `http://127.0.0.1:8000/docs` | FastAPI 文档 |
| Vite 开发端口 | `http://127.0.0.1:5173/` | 仅前端开发时使用，不是生产入口 |

## 快速启动

### Docker（推荐）

```bash
docker-compose up -d
```

Dashboard UI 在 `http://127.0.0.1:8091/`，Gateway API 在 `http://127.0.0.1:8000/`。

### 手动安装

#### 1. 安装依赖

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
```

#### 2. 配置环境

```bash
cp .env.example .env
```

运行时优先级：

1. `.env`
2. `data/system_config.json`
3. `config/config.yaml`

#### 3. 启动 Dashboard 主服务

```bash
python -m src.dashboard_server --host 127.0.0.1 --port 8091
```

打开：

- `http://127.0.0.1:8091/` 看管理界面
- `http://127.0.0.1:8091/healthz` 看健康检查

#### 4. 可选：启动 Gateway Service

```bash
pip install -e services/common -e services/gateway-service
cd services/gateway-service
../../venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## 测试与校验

```bash
# Python 后端测试
./venv/bin/python -m pytest tests/ -q

# Python lint
ruff check src/

# 前端构建
cd client && npm run build

# 前端测试
cd client && npm test
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
services/
  gateway-service/          Open Platform 适配网关（FastAPI）
  common/                   服务间共享库（Pydantic config 等）
src/                        Python 单体业务与 Dashboard 服务
tests/                      pytest 测试
```

## 文档

- [QUICKSTART.md](./QUICKSTART.md)
- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [CHANGELOG.md](./CHANGELOG.md)
- [docs/API.md](./docs/API.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

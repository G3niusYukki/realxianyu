# XianyuFlow | 闲流

[![CI](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml/badge.svg)](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

闲鱼运营自动化工具，覆盖消息自动回复、智能报价、订单履约、商品上架、Cookie 管理和运维诊断。

**当前版本：v10.1.0**

## 架构概览

v10 采用单体 + 网关的简化架构：

- **Python 单体**（`src/`）：Dashboard 服务、消息处理、报价引擎、订单管理等全部业务逻辑
- **Gateway Service**（`services/gateway-service`）：Open Platform 适配网关，独立 FastAPI 服务
- **React 前端**（`client/`）：Vite + Tailwind 构建的管理界面，由 Dashboard 服务托管

## 核心特性

| 特性 | 说明 |
|------|------|
| **多级 Cookie 降级保活** | 闲管家 IM 直读 → CookieCloud 同步 → 本地直读 → DrissionPage 硬解，四级降级 |
| **现代化前后端分离** | React + TailwindCSS Dashboard，状态监控与配置热更新 |
| **AI 智能客服** | 接入大语言模型（DeepSeek 等），自动报价与智能上下文回复 |
| **虚拟商品全自动核销** | 卡密自动发货，自动标记已发货，状态全链路闭环 |
| **闲管家深度集成** | 兼容闲管家 PC 端登录状态，双重签名算法，降低纯 Web 协议风控概率 |

## 近期可靠性修复（2026-03）

- **Token/RGV587 恢复增强**：当 `token` 接口遇到 `FAIL_SYS_USER_VALIDATE` / `RGV587` 时，会主动刷新 Cookie（优先 BitBrowser，未启用时走 IM 路径）并重试，减少“未启用 BitBrowser 即不可用”的情况。
- **MTOP 风控响应显式失败**：消息发送链路会识别并标记 `risk_control`，不再把风控拦截误判为发送成功。
- **报价降级可观测**：`api_cost_plus_markup` 并行回退会保留 `fallback_reason`、`fallback_source` 与 `failure_class`，便于定位慢接口/网络故障。
- **配置读取不再静默吞错**：关键配置读取异常改为显式上抛或告警日志，避免“假成功”降级掩盖真实问题。

## 架构设计

```
┌──────────────────────────────────────────────────────────┐
│                     前端层  client/                        │
│     React + TailwindCSS SPA，编译后由后端服务静态托管     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│            网关层  src/dashboard_server.py                │
│      BaseHTTPRequestHandler · 路由分发 + 静态服务        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│           业务中枢  src/dashboard/mimic_ops.py            │
│             Facade 代理 (~3000 行)                       │
└────┬────────────────┬──────────────────┬────────────────┘
     │                │                  │
┌────▼────┐   ┌──────▼───┐   ┌────────▼─────────┐
│ dashboard/ │   │  modules/ │   │   cli/         │
│ services/  │   │           │   │                 │
│Cookie    │   │Messages   │   │cmd_main.py      │
│Service   │   │Orders     │   │cmd_orders.py    │
│XGJ       │   │Quote      │   │cmd_module.py   │
│Service   │   │Listing    │   │cmd_quote.py    │
│          │   │Virtual    │   │                 │
│          │   │Goods      │   │                 │
└──────────┘   └───────────┘   └─────────────────┘
```

### 核心设计原则

- **Facade 模式**：`mimic_ops.py` 仅作分发代理，不含业务逻辑
- **YAML 单一真相**：`config/config.yaml` 是唯一默认值来源，无需手动同步
- **无 global 声明**：全局状态通过单例类（`WebSocketTransportManager`、`QuoteLedger` 等）管理
- **CLI 模块化**：`cli/` 包按职责拆分，支持猴子补丁测试

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
# 可选：lint/类型检查工具
pip install -r requirements-dev.txt
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

## 测试与规范

```bash
# Python 后端测试
./venv/bin/python -m pytest tests/ -q

# Python lint（需先安装 requirements-dev.txt）
./venv/bin/python -m ruff check src/ services/

# Python format check
./venv/bin/python -m ruff format src/ services/ --check

# 前端构建
cd client && npm run build

# 前端测试
cd client && npm test
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

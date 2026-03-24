# Xianyu Guanjia (闲鱼管家)

[![CI](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml/badge.svg)](https://github.com/G3niusYukki/realxianyu/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-9.5.0-green.svg)](./CHANGELOG.md)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **⚠️ 架构变更通知 (v8.1.0+)**
>
> 本项目已进行深度重构，**废弃了所有"一键安装 (.bat/.sh)"和冗余的内置 HTML 打包方式**，全面转向现代化的 **前端 (React/Vite) + 后端 (Python Asyncio)** 分离架构。
>
> 本项目旨在作为工作室内部部署和 AI Agent 自动化驱动的基础设施。不再面向无编程基础的 C 端用户提供"双击启动包"。

---

## 📚 文档导航

| 文档 | 说明 | 目标读者 |
|------|------|----------|
| [QUICKSTART.md](./QUICKSTART.md) | 5分钟快速启动 | 新用户 |
| [USER_GUIDE.md](./USER_GUIDE.md) | 详细使用说明书 | 终端用户 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构设计 | 开发者 |
| [docs/API.md](./docs/API.md) | HTTP API 文档 | 前后端开发者 |
| [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) | 生产部署指南 | 运维人员 |
| [docs/for-agents/index.md](./docs/for-agents/index.md) | AI Agent 开发指南 | AI Agent |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | 贡献指南 | 贡献者 |

---

## 🚀 核心特性

| 特性 | 说明 |
|------|------|
| **多级 Cookie 降级保活** | 闲管家 IM 直读 → CookieCloud 同步 → 本地直读 → Playwright 硬解，四级降级 |
| **现代化前后端分离** | React + TailwindCSS Dashboard，状态监控与配置热更新 |
| **AI 智能客服** | 接入大语言模型（DeepSeek 等），自动报价与智能上下文回复 |
| **虚拟商品全自动核销** | 卡密自动发货，自动标记已发货，状态全链路闭环 |
| **闲管家深度集成** | 兼容闲管家 PC 端登录状态，双重签名算法，降低纯 Web 协议风控概率 |

---

## 💻 快速部署

> 详细部署指南请参阅 [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) | AI Agent 专用指南 [AGENT_DEPLOYMENT.md](./AGENT_DEPLOYMENT.md)

```bash
# 1. 构建前端
cd client && npm install && npm run build && cd ..

# 2. 初始化后端
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 填入 XIANYU_COOKIE_1、DEEPSEEK_API_KEY 等必要参数

# 4. 启动
python -m src.main
```

---

## 🏗 架构设计

```
┌──────────────────────────────────────────────────────────┐
│                     前端层  client/                        │
│     React + TailwindCSS SPA，编译后由后端服务静态托管     │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│              网关层  dashboard_server.py                  │
│      BaseHTTPRequestHandler · 路由分发 + 静态服务        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│           业务中枢  src/dashboard/mimic_ops.py            │
│             Facade 代理 (~3000 行)                       │
└────┬────────────────┬──────────────────┬────────────────┘
     │                │                  │
┌────▼────┐   ┌──────▼───┐   ┌────────▼─────────┐
│ Services/│   │  Modules/ │   │   CLI 包 cli/    │
│          │   │           │   │                 │
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

---

## 🧪 测试与规范

```bash
# 运行全部测试（~1172 个）
./venv/bin/python -m pytest tests/ -q

# 代码规范检查
ruff check src/ --extend-ignore I001,E501,UP012,RUF100
ruff format --check src/
```

提交前请确保测试全部通过且 `ruff check` 无报错。

---

## 📂 目录结构

```
src/
├── core/               # 核心基础设施（配置、日志、浏览器客户端）
├── services/           # 核心业务服务（CookieService / XGJService）
├── modules/            # 业务模块
│   ├── messages/       #   WS 长连接、消息回复、workflow
│   ├── orders/         #   订单履约、自动改价
│   ├── quote/         #   物流报价引擎
│   ├── listing/       #   商品上架
│   └── virtual_goods/ #   虚拟商品核销
├── integrations/       # 闲管家 API 集成
├── dashboard/          # Dashboard Facade + HTTP Routes
├── dashboard/services/ # 从 mimic_ops 拆分的服务
├── cli/               # 模块化 CLI 包
├── dashboard_server.py # HTTP 服务器入口
├── main.py            # Python 程序主入口
└── setup_wizard.py    # 初始化向导
```

---

## 📜 许可协议

[MIT License](./LICENSE)

<div align="center">

# 🦞 Xianyu OpenClaw

**闲鱼卖家自动化工作台：消息、报价、订单、虚拟商品、闲管家与运维面板一体化**

[![CI](https://github.com/G3niusYukki/xianyu-openclaw/actions/workflows/ci.yml/badge.svg)](https://github.com/G3niusYukki/xianyu-openclaw/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[快速开始](#-快速开始) · [部署文档](docs/DEPLOYMENT.md) · [用户指南](USER_GUIDE.md) · [更新日志](CHANGELOG.md)

</div>

---

## 项目现状

当前仓库已经演进为一个 **多运行时、模块化、可视化** 的闲鱼自动化工作台，核心能力包括：

- **消息自动化**：WebSocket / DOM / auto 三种传输模式，自动回复、双层去重、议价识别、人工接管、会话工作流
- **自动报价**：成本表导入、地理归一化、远程报价源回退、缓存与熔断
- **订单履约**：订单状态同步、售后模板、实物物流发货、闲管家开放平台对接
- **虚拟商品闭环**：回调接入、事件去重、调度执行、重放与人工兜底
- **运营模块**：自动调价、擦亮、数据统计、增长实验与合规中心
- **Dashboard**：配置中心、模块状态、Cookie 健康、闲管家控制面板、订单回调入口、手动重试操作
- **多平台部署**：本地一键启动、Docker Compose、Windows EXE / bat 脚本、macOS launchd 守护

> 如果你之前看过旧版文档：项目已不再只是“v2.0 的虚拟商品自动化平台”，当前主线已经覆盖 **6.x 系列能力**，并且正在进入以订单闭环和控制台完善为主的阶段。

---

## ✨ 核心能力

### 1) 售前消息自动化

- 自动识别咨询、议价、下单意图
- 支持标准格式回复与非空回复兜底
- 双层去重：精确 hash + 内容 hash
- 支持会话上下文记忆、人工接管与恢复
- 支持 workflow worker、SLA 基准测试与首响指标

### 2) 自动报价

- 本地 Excel / CSV 成本表导入
- 省市名称归一化与模糊匹配
- API 成本源 + 本地规则双路径
- TTL 缓存、stale-while-revalidate、熔断降级
- CLI 可直接做 health / candidates / setup

### 3) 订单与闲管家集成

- 闲管家开放平台签名与 API 适配层
- 实物订单可走 API 改价 / API 发货
- 支持 Dashboard 中保存 AppKey / AppSecret
- 支持支付后回调：`/api/orders/callback`
- 发货失败时可降级为人工发货任务，避免假阳性完成态

### 4) 虚拟商品闭环

- 回调入站与事件去重
- 调度器批处理、事件重放、人工接管
- 适合卡密、兑换码、虚拟交付类场景

### 5) 运维与治理

- Cookie 健康检查与浏览器侧续期
- 合规策略中心、审计与重放
- AI 调用成本统计
- 增长实验与漏斗分析
- 模块化启动：`presales / operations / aftersales`

---

## 🏗️ 当前架构

```text
React/Vite 前端 (client)
  └─ 管理面板 / 配置中心 / 状态页 / 运营页面

Node.js 后端 (server)
  └─ 轻量 API 层 / 配置接口 / 前端联动

Python 核心后端 (src)
  ├─ Dashboard HTTP 服务
  ├─ Messages / Quote / Orders / Virtual Goods / Operations
  ├─ Xianguanjia integration
  ├─ Cookie / Compliance / Growth / Analytics
  └─ CLI + 模块化守护进程
```

### 关键目录

```text
xianyu-openclaw/
├── client/                     # React + Vite 前端
├── server/                     # Node.js API 层
├── src/                        # Python 核心后端
│   ├── cli.py                  # 统一 CLI 入口
│   ├── dashboard_server.py     # Dashboard HTTP 服务
│   ├── integrations/xianguanjia/
│   └── modules/
│       ├── messages/
│       ├── quote/
│       ├── orders/
│       ├── virtual_goods/
│       ├── operations/
│       ├── growth/
│       └── compliance/
├── config/                     # 配置样例
├── docs/                       # 部署与补充文档
├── scripts/                    # macOS / Unix / Windows 辅助脚本
└── tests/                      # 回归与覆盖测试
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- npm
- Chrome / Edge（Cookie 自动获取、Playwright 浏览器能力相关）
- 闲鱼 Cookie
- AI API Key（如需自动回复 / 内容生成）

### 方式一：本地一键启动

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
cp .env.example .env

# macOS / Linux
./start.sh

# Windows
start.bat
```

启动脚本会自动：

1. 创建 Python 虚拟环境
2. 安装 Python / Node.js 依赖
3. 安装 Playwright Chromium
4. 启动：
   - React 前端：`http://localhost:5173`
   - Node 后端：`http://localhost:3001`
   - Python Dashboard：`http://localhost:8091`

### 方式二：手动启动

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cd server && npm install && cd ..
cd client && npm install && cd ..

cp .env.example .env

python -m src.dashboard_server --port 8091
npm run dev:server
npm run dev:client
```

### 方式三：Docker Compose

```bash
cp .env.example .env
docker compose up -d
```

详细部署见：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## ⚙️ 最小配置

`.env` 里至少建议配置：

```bash
XIANYU_COOKIE_1=your_cookie_here

AI_PROVIDER=deepseek
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

XGJ_APP_KEY=
XGJ_APP_SECRET=
XGJ_BASE_URL=https://open.goofish.pro
```

说明：

- `XIANYU_COOKIE_1`：闲鱼登录 Cookie
- `AI_*`：自动回复 / 内容生成使用的业务模型
- `XGJ_*`：闲管家开放平台配置，用于订单/物流等链路

---

## 🧭 常用 CLI

项目当前的 CLI 已覆盖主要运维和业务能力：

```bash
# 系统体检
python -m src.cli doctor --strict

# 售前 / 运营 / 售后模块检查
python -m src.cli module --action check --target all
python -m src.cli module --action status --target all

# 启动售前 worker
python -m src.cli module --action start --target presales --mode daemon --background

# 消息自动回复 / SLA 基准
python -m src.cli messages --action auto-reply --limit 20 --dry-run
python -m src.cli messages --action sla-benchmark --benchmark-count 120

# 报价健康检查
python -m src.cli quote --action health

# 订单履约 / 发货
python -m src.cli orders --action trace --order-id ORDER_ID
python -m src.cli orders --action deliver --order-id ORDER_ID --waybill-no SF123

# 虚拟商品回调调度
python -m src.cli virtual-goods --action scheduler --dry-run
```

---

## 🖥️ Dashboard 当前重点能力

Dashboard 不只是“看板”，现在也是主要的运维入口之一：

- Cookie 配置与健康状态
- AI 服务配置
- 闲管家配置区（AppKey / AppSecret / 自动改价 / 自动发货 / 支付后自动触发）
- 订单回调入口显示：`/api/orders/callback`
- API 改价 / API 发货手动重试
- 模块状态与恢复入口

健康检查接口：

- Python Dashboard：`GET /healthz`
- Node.js 后端：`GET /health`

---

## 🧪 测试与质量

```bash
pytest tests/
ruff check src tests
ruff format src tests

# 前端构建
cd client && npm run build
```

项目包含大量覆盖测试，重点覆盖消息、报价、订单、Dashboard、虚拟商品与针对性回归路径。

---

## 📦 发布说明

当前文档对应的是 **6.2.5 文档线**，重点反映以下最新变化：

- Dashboard 闲管家控制面板补齐
- ` /api/orders/callback ` 订单支付后触发链路补齐
- 实物订单在未真正提交物流单时保持 `processing`
- 文档统一到当前仓库结构、脚本、模块和端点

如需查看历史变更，请阅读 [CHANGELOG.md](CHANGELOG.md)。

---

## 🤝 贡献

欢迎提 Issue / PR。

```bash
git checkout -b feature/your-change
# 修改后运行测试
git commit -m "docs: update project documentation"
git push origin feature/your-change
```

---

## ⚠️ 免责声明

本项目仅供学习、研究和合法合规的业务自动化实践使用。请遵守闲鱼平台规则及所在地法律法规，Cookie、API Key 与回调数据需妥善保管。

---

## 📄 License

MIT

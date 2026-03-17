<div align="center">

# 闲鱼管家

[![Version](https://img.shields.io/badge/version-8.0.0-blue.svg)](CHANGELOG.md)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**闲鱼虚拟商品卖家 7×24 无人值守自动化工作台**

WebSocket 直连消息通道 · AI 智能回复与报价 · 商品管理与订单履约 · 风控自愈

</div>

---

## 功能亮点

| 能力 | 说明 |
|------|------|
| **消息自动回复** | WebSocket 毫秒级接收，AI 意图识别（咨询/议价/下单），30+ 意图规则，双层去重 |
| **智能报价引擎** | 地址解析 + 快递计费 + 时效匹配，报价安全加价可配置 |
| **商品自动上架** | AI 生成标题描述，7 套视觉模板，HTML→截图→OSS→API 发布 |
| **订单自动履约** | 虚拟商品自动发卡密，闲管家 API 物流同步，售后自动识别 |
| **风控自动恢复** | 滑块自动验证（Playwright + OpenCV），CookieCloud 即时同步，Cookie 静默刷新 |
| **监控与告警** | 服务健康面板，Cookie/AI/API 实时检测，飞书/企业微信多渠道推送 |
| **一键在线更新** | Dashboard 内检查更新 → 备份 → 下载 → 重启，全自动完成 |
| **敏感词脱敏** | Dashboard 可配置替换规则，回复自动替换敏感词 |

---

## 快速开始

### 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| Node.js | 18+（仅前端构建需要） |
| 操作系统 | macOS / Windows / Linux |

### 三项准备

| 必备项 | 说明 | 获取方式 |
|--------|------|---------|
| **闲鱼 Cookie** | 登录凭证 | 浏览器 F12 复制，或启动后在管理面板自动获取 |
| **AI API Key** | 自动回复 | 推荐 [DeepSeek](https://platform.deepseek.com)（性价比高） |
| **闲管家凭证** | 订单/发货 | [闲管家开放平台](https://open.goofish.pro) 注册获取 |

### 方式一：离线安装包部署（推荐）

从 [Releases](https://github.com/brianzhibo-design/XIANYUGUANJIA/releases) 下载对应平台的安装包：

```bash
# macOS
tar xzf xianyu-openclaw-v8.0.0-macos-arm64.tar.gz
cd xianyu-openclaw-v8.0.0
bash quick-start.sh

# Windows
# 解压 xianyu-openclaw-v8.0.0-windows-x64.zip → 双击 quick-start.bat
```

安装包已包含全部依赖，无需联网安装。首次启动自动弹出设置向导。

### 方式二：Docker 部署

```bash
cp .env.example .env
# 编辑 .env，填入 Cookie、AI Key、闲管家凭证

docker compose up -d                          # 国际网络
MIRROR=china docker compose up -d --build     # 国内网络
```

### 方式三：一键启动脚本

```bash
./start.sh     # macOS / Linux
start.bat      # Windows
```

### 方式四：手动安装

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cd client && npm install && npm run build && cd ..

cp config.example.yaml config/config.yaml
# 编辑 config/config.yaml 填入配置

# 启动（需要 2 个终端）
python -m src.dashboard_server --port 8091   # 终端 1: 后端
cd client && npx vite --host                 # 终端 2: 前端
```

### 访问地址

- **管理面板**: http://localhost:5173
- **后端 API**: http://localhost:8091

---

## 首次配置

首次启动会自动弹出 **SetupWizard 设置向导**，按步骤完成：

1. **账户管理** → 粘贴 Cookie 或点击「自动获取」
2. **系统配置 → AI** → 选择服务商（DeepSeek/通义千问/智谱等），填入 API Key
3. **系统配置 → CookieCloud** → 填入浏览器扩展的 UUID 和密码（推荐）
4. **消息 → 对话沙盒** → 测试自动回复效果
5. 确认无误后开启自动回复

---

## 在线更新

Dashboard 右上角显示当前版本号和「检查更新」按钮：

1. 点击「检查更新」，系统自动比对 GitHub Release 最新版本
2. 发现新版本后点击「立即更新」
3. 系统自动完成：备份当前版本 → 下载更新包 → 解压覆盖 → 安装依赖 → 重启服务

更新过程中 Dashboard 实时显示进度，服务重启后自动重连。

---

## 常见问题

### Cookie 频繁失效 / WebSocket 断连

1. 保持本机浏览器已登录闲鱼，系统会自动读取最新 Cookie
2. 推荐安装 [CookieCloud](https://github.com/nichenqin/CookieCloud) 浏览器扩展，实现 Cookie 即时同步
3. 如无法保持浏览器登录，可在 Dashboard 手动粘贴 Cookie

### RGV587 风控滑块触发

1. **推荐** — CookieCloud：浏览器中手动通过滑块验证后，Cookie 自动同步
2. **自动** — 系统设置中开启「风控滑块自动验证」（有封号风险，谨慎使用）
3. **手动** — 在 Dashboard「账户管理」粘贴新 Cookie

### macOS 桌面快捷方式无法启动

确认 `start.sh` 有执行权限：`chmod +x start.sh`。如果终端闪退，检查 Python 和 Node.js 是否在 PATH 中。

### Windows Playwright 安装失败

1. 确认网络可访问 `cdn.playwright.dev`
2. 网络受限时设置代理：`set HTTPS_PROXY=http://proxy:port` 后重试
3. 使用离线安装包部署可跳过此步骤

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                React 前端 (Vite + TypeScript)            │
│  Dashboard · 商品管理 · 订单中心 · 系统配置 · 数据分析   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────┴────────────────────────────────┐
│                 Python 后端 (asyncio)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ WebSocket │ │ AI 回复  │ │ 报价引擎 │ │ 任务调度 │   │
│  │ 消息监听  │ │ 意图识别 │ │ 地址解析 │ │ 自动发货 │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Cookie   │ │ 滑块验证 │ │ 告警通知 │ │ 在线更新 │   │
│  │ 自动刷新  │ │ 风控自愈 │ │ 飞书/企微 │ │ 版本管理 │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | React 18 / Vite / TailwindCSS / TypeScript | 响应式管理面板 |
| **后端** | Python 3.10+ / asyncio | 消息、AI、报价、配置、更新 |
| **数据库** | SQLite (WAL) | 零配置，内嵌运行 |
| **消息通道** | WebSocket 直连闲鱼 | 毫秒级接收 |
| **AI 服务** | OpenAI 兼容 API | DeepSeek / 通义千问 / 智谱 / 火山方舟 |
| **通知** | HTTP Webhook | 飞书 / 企业微信 |

---

## 项目结构

```
XIANYUGUANJIA/
├── src/                           # Python 后端
│   ├── __init__.py                # 版本号定义 (__version__)
│   ├── dashboard_server.py        # Dashboard HTTP 服务入口
│   ├── main.py                    # 主入口
│   ├── core/                      # 核心模块
│   │   ├── config.py              # 配置加载
│   │   ├── cookie_health.py       # Cookie 健康检查
│   │   ├── cookie_grabber.py      # Cookie 自动刷新
│   │   ├── slider_solver.py       # 滑块自动验证
│   │   ├── notify.py              # 告警通知
│   │   ├── update_config.py       # 在线更新配置
│   │   └── playwright_client.py   # 浏览器自动化
│   ├── dashboard/                 # Dashboard 服务层
│   │   ├── routes/                # API 路由
│   │   ├── config_service.py      # 配置管理
│   │   └── repository.py          # 数据仓库
│   └── modules/                   # 业务模块
│       ├── messages/              # 消息（回复、去重、议价）
│       ├── listing/               # 商品（上架、模板、图片）
│       ├── orders/                # 订单（同步、发货）
│       ├── quote/                 # 报价引擎
│       └── accounts/              # 账号管理
├── client/                        # React 前端 (TypeScript)
│   └── src/
│       ├── pages/                 # 页面组件
│       └── components/            # 通用组件
├── scripts/                       # 部署与运维脚本
│   ├── build_release.sh           # 构建安装包
│   ├── update.sh / update.bat     # 在线更新脚本
│   └── prepare_offline.sh         # 离线依赖打包
├── config/                        # 配置文件
│   └── config.example.yaml        # 配置示例
├── tests/                         # 测试
├── start.sh / start.bat           # 一键启动
├── quick-start.sh / .bat          # 首次安装引导
├── supervisor.sh                  # 进程守护
└── docker-compose.yml             # Docker 编排
```

---

## 开发指南

```bash
# 启动后端（终端 1）
python -m src.dashboard_server --port 8091

# 启动前端（终端 2）
cd client && npx vite --host

# 测试
pytest tests/ --cov=src --cov-report=html

# 代码检查
ruff check src/
ruff format src/

# 构建前端
cd client && npm run build

# 构建安装包
bash scripts/build_release.sh
```

版本号规范和贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

完整更新日志见 [CHANGELOG.md](CHANGELOG.md)。

---

## 免责声明

本软件为私有软件，未经授权禁止分发、复制或用于商业用途。使用者需遵守闲鱼平台规则和相关法律法规，自行承担使用风险。

---

<div align="center">

闲鱼管家 v8.0.0

</div>

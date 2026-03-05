# 部署指南

> 🐳 完整的 xianyu-openclaw 部署方案

---

## 📋 部署方式概览

本项目支持多种部署方式，根据你的需求选择：

| 部署方式 | 适用场景 | 难度 | 文档位置 |
|---------|---------|------|---------|
| **Docker Compose** | 生产环境、多平台 | ⭐⭐ 中等 | 本文件第 3 节 |
| **Windows EXE** | Windows 小白用户 | ⭐ 简单 | [QUICKSTART.md](../QUICKSTART.md) |
| **Lite 模式** | 开发测试、无 Docker 环境 | ⭐⭐ 中等 | 本文件第 5 节 |
| **模块化部署** | 大规模生产、分离运维 | ⭐⭐⭐ 困难 | 本文件第 7 节 |

---

## 🔧 环境要求

### 必需组件

- **Docker Engine**: 20.10+ [安装指南](https://docs.docker.com/get-docker/)
- **Docker Compose**: 2.0+（通常随 Docker Desktop 安装）
- **Git**: 用于克隆仓库

### AI 服务密钥（至少选择一个）

**网关 AI（OpenClaw Gateway 必需）：**
- Anthropic (Claude)
- OpenAI (GPT)
- Moonshot (Kimi)
- MiniMax
- ZAI (智谱)

**业务文案 AI（可选，推荐）：**
- DeepSeek
- 阿里百炼
- 火山方舟
- 智谱

### 其他要求

- **闲鱼账号**：已注册且可正常登录
- **Cookie 获取能力**：需要从浏览器复制 Cookie
- **可选**：域名、SSL 证书（生产环境推荐）

---

## 🚀 标准 Docker Compose 部署

### 1. 克隆仓库

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，参考以下生产环境配置：

```bash
# === 网关 AI 配置（必须，至少填一个）===
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
# 或
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# === OpenClaw 网关配置 ===
OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)  # 生成随机密钥
OPENCLAW_WEB_PORT=8080
AUTH_PASSWORD=$(openssl rand -hex 16)           # 生成随机密码
AUTH_USERNAME=admin

# === 闲鱼 Cookie ===
XIANYU_COOKIE_1=your_production_cookie_here

# === 业务文案 AI（推荐 DeepSeek，性价比高）===
AI_PROVIDER=deepseek
AI_API_KEY=sk-xxxxxxxxxxxx
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
AI_TEMPERATURE=0.7

# === 数据库 ===
DATABASE_URL=sqlite:///data/agent.db
```

### 3. 启动服务

```bash
# 启动所有服务（后台运行）
docker compose up -d

# 查看启动日志
docker compose logs -f
```

### 4. 验证部署

```bash
# 检查容器状态
docker compose ps

# 预期输出：
# NAME              STATUS
# xianyu-openclaw   Up (healthy)

# 健康检查端点
curl http://localhost:8080/healthz

# 预期返回：{"status":"ok"}
```

### 5. 首次配对（如需要）

```bash
# 查看待配对设备
docker compose exec -it openclaw-gateway openclaw devices list

# 批准配对请求
docker compose exec -it openclaw-gateway openclaw devices approve <request_id>
```

---

## ⚙️ docker-compose.yml 详解

```yaml
services:
  openclaw-gateway:
    image: coollabsio/openclaw:latest    # 官方 OpenClaw 镜像
    container_name: xianyu-openclaw
    ports:
      - "${OPENCLAW_WEB_PORT:-8080}:8080"  # Web 界面端口
    volumes:
      # 代码和配置挂载
      - ./skills:/home/node/.openclaw/workspace/skills
      - ./src:/home/node/.openclaw/workspace/src
      - ./config:/home/node/.openclaw/workspace/config
      - ./data:/home/node/.openclaw/workspace/data
      - ./requirements.txt:/home/node/.openclaw/workspace/requirements.txt
      # 旧版路径兼容
      - ./skills:/data/workspace/skills
      - ./src:/data/workspace/src
      - ./config:/data/workspace/config
      - ./data:/data/workspace/data
      - ./requirements.txt:/data/workspace/requirements.txt
      # 初始化脚本
      - ./scripts/init.sh:/app/config/init.sh
      # 持久化状态
      - openclaw-state:/home/node/.openclaw
      - openclaw-state:/data/.openclaw
    env_file:
      - .env
    environment:
      - HOME=/home/node
      - TERM=xterm-256color
      - OPENCLAW_GATEWAY_TOKEN=${OPENCLAW_GATEWAY_TOKEN:-}
      - OPENCLAW_CUSTOM_INIT=/app/config/init.sh
    init: true
    restart: unless-stopped              # 自动重启策略
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://127.0.0.1:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  openclaw-state:                       # 命名卷，持久化数据
```

### 关键配置说明

| 配置项 | 说明 | 建议 |
|-------|------|------|
| `restart: unless-stopped` | 容器异常退出时自动重启 | 生产环境必开 |
| `healthcheck` | 健康检查机制 | 每 30 秒检查一次 |
| `volumes` | 持久化存储 | 重要数据不要放容器内 |
| `init: true` | 使用 init 进程管理 | 防止僵尸进程 |

---

## 🖥️ Lite 模式部署（无 Docker）

适用于无法使用 Docker 的环境，或需要直接调试的场景。

### 环境要求

- Python 3.10+
- pip
- Playwright（会自动安装浏览器）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器
playwright install chromium

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要配置
```

### 启动 Lite 模式

```bash
# 启动 Lite 运行时
python -m src.lite

# 或使用脚本
./scripts/lite_start.sh        # macOS/Linux
scripts\windows\lite_quickstart.bat  # Windows
```

### Lite 模式 vs Docker 模式对比

| 特性 | Lite 模式 | Docker 模式 |
|-----|-----------|-------------|
| 安装难度 | 需配置 Python 环境 | 仅需 Docker |
| 资源占用 | 较低 | 中等 |
| 稳定性 | 依赖本地环境 | 容器隔离，更稳定 |
| 适用场景 | 开发测试 | 生产环境 |
| 自动重启 | 需配置 systemd/launchd | Docker 自动管理 |
| 多平台 | 需单独配置 | 统一镜像 |

---

## 🪟 Windows 部署

### 方式 1：EXE 图形化工具（推荐）

1. 确保已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. 从 [Releases](https://github.com/G3niusYukki/xianyu-openclaw/releases) 下载 `xianyu-openclaw-launcher.zip`
3. 解压并双击运行
4. 按向导完成配置

### 方式 2：批处理脚本

```bat
# 在项目根目录执行

# 快速启动
scripts\windows\quickstart.bat

# 完整菜单
scripts\windows\launcher.bat

# 单独启动模块
scripts\windows\start_presales.bat daemon 20 5
scripts\windows\start_operations.bat daemon 30
scripts\windows\start_aftersales.bat daemon 20 15 delay

# 查看状态
scripts\windows\module_status.bat
scripts\windows\module_check.bat

# 诊断
scripts\windows\doctor.bat
```

### Windows 常用脚本清单

项目提供了 35+ 个 Windows 批处理脚本，位于 `scripts/windows/`：

| 脚本 | 用途 |
|------|------|
| `quickstart.bat` | 一键安装+检查+启动 |
| `launcher.bat` | 交互式菜单 |
| `setup_windows.bat` | Windows 环境配置 |
| `build_exe.bat` | 构建 EXE 工具 |
| `start_all_lite.bat` | 启动所有 Lite 模块 |
| `module_check.bat` | 模块健康检查 |
| `module_status.bat` | 查看模块状态 |
| `module_stop.bat` | 停止模块 |
| `module_recover.bat` | 恢复模块 |
| `doctor.bat` | 系统诊断 |
| `dashboard.bat` | 启动数据看板 |

---

## 🍎 macOS/Linux 部署

### 使用 Unix 脚本

```bash
# 启动所有 Lite 模块
./scripts/unix/start_all_lite.sh

# 启动数据看板
./scripts/unix/dashboard.sh 8091

# 恢复售前模块
./scripts/unix/recover_presales.sh
```

### macOS 开机自启（launchd）

```bash
# 安装为系统服务
./scripts/macos/install_service.sh install

# 卸载服务
./scripts/macos/install_service.sh uninstall
```

服务将在系统启动时自动运行，崩溃后自动重启。

---

## 🧩 模块化部署

对于大规模生产环境，可以按业务模块分离部署：

### 模块说明

| 模块 | 职责 | 启动命令 |
|------|------|---------|
| **presales** | 售前（消息自动回复、报价） | `python -m src.cli module --action start --target presales` |
| **operations** | 运营（擦亮、调价、上下架） | `python -m src.cli module --action start --target operations` |
| **aftersales** | 售后（订单处理、退款） | `python -m src.cli module --action start --target aftersales` |

### 独立启动示例

```bash
# 启动售前模块（守护进程模式）
python -m src.cli module --action start \
  --target presales \
  --mode daemon \
  --limit 20 \
  --interval 5

# 启动运营模块
python -m src.cli module --action start \
  --target operations \
  --mode daemon \
  --init-default-tasks \
  --interval 30

# 启动售后模块
python -m src.cli module --action start \
  --target aftersales \
  --mode daemon \
  --limit 20 \
  --interval 15 \
  --issue-type delay
```

### 模块管理命令

```bash
# 查看所有模块状态
python -m src.cli module --action status --target all

# 停止所有模块
python -m src.cli module --action stop --target all

# 恢复模块（停止→清理→重启）
python -m src.cli module --action recover --target presales

# 查看模块日志
python -m src.cli module --action logs --target all --tail-lines 100

# Cookie 健康检查
python -m src.cli module --action cookie-health
```

---

## 🔒 生产环境加固

### 1. 使用反向代理（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 2. 自动备份

使用提供的备份脚本：

```bash
# 手动备份
./scripts/backup_data.sh

# 添加到 cron（每天凌晨 2 点备份）
0 2 * * * /path/to/xianyu-openclaw/scripts/backup_data.sh
```

备份内容：
- `data/` 目录（数据库、配置）
- 7 天自动轮转

### 3. 监控告警

配置飞书 webhook：

```bash
python -m src.cli automation --action setup \
  --enable-feishu \
  --feishu-webhook "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx"

# 测试告警
python -m src.cli automation --action test-feishu
```

告警触发条件：
- Workflow 启动/停止
- Cookie 失效
- SLA 阈值突破
- 系统异常

### 4. 日志管理

```bash
# 查看实时日志
docker compose logs -f --tail 100

# 导出日志到文件
docker compose logs > xianyu-$(date +%Y%m%d).log

# 清理旧日志（保留 7 天）
find . -name "*.log" -mtime +7 -delete
```

---

## 🔍 故障排查

### 容器无法启动

```bash
# 查看详细错误
docker compose logs --tail 50

# 检查端口占用
lsof -ti:8080 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8080   # Windows

# 重置容器
docker compose down
docker compose up -d
```

### Cookie 失效

```bash
# 检查 Cookie 有效性
python -m src.cli doctor --strict

# 或
python -m src.cli module --action cookie-health
```

### AI 服务异常

```bash
# 查看网关日志
docker compose logs openclaw-gateway --tail 100

# 检查 API Key 余额
# 登录对应的 AI 服务控制台查看
```

### 数据卷权限问题

```bash
# Linux/macOS 修复权限
sudo chown -R $(whoami):$(whoami) data/
sudo chown -R $(whoami):$(whoami) logs/

# Docker 方式修复
docker compose exec openclaw-gateway chown -R node:node /home/node/.openclaw
```

---

## 📊 性能优化

### 资源限制（可选）

在 `docker-compose.yml` 中添加：

```yaml
services:
  openclaw-gateway:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 数据库优化

SQLite 配置（已默认启用）：
- WAL 模式（并发写入优化）
- busy_timeout（避免锁等待）

---

## 🔄 更新升级

### 更新到最新版本

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 拉取最新镜像
docker compose pull

# 3. 重启服务
docker compose down
docker compose up -d

# 4. 验证
docker compose ps
```

### 回滚版本

```bash
# 查看历史版本
git log --oneline

# 回滚到特定版本
git checkout <commit-hash>
docker compose down
docker compose up -d
```

---

## 📞 获取帮助

- 📖 **用户指南**：[USER_GUIDE.md](../USER_GUIDE.md)
- 🚀 **快速开始**：[QUICKSTART.md](../QUICKSTART.md)
- 🔧 **CLI 文档**：[API.md](API.md)
- 🐛 **问题反馈**：[GitHub Issues](https://github.com/G3niusYukki/xianyu-openclaw/issues)

---

<p align="center">
  部署遇到问题？查看 <a href="../USER_GUIDE.md">用户指南</a> 或提交 Issue
</p>

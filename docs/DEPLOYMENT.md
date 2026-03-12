# 部署指南

本文档以当前仓库的真实结构与脚本为准，覆盖本地、Docker、Windows 和模块化部署。

---

## 部署方式一览

| 方式 | 适用场景 | 入口 |
|------|----------|------|
| 本地一键启动 | 开发、单机试跑、个人运维 | `./start.sh` / `start.bat` |
| 手动本地启动 | 需要拆分终端、调试服务 | Python + Node + Vite |
| Docker Compose | 测试环境、统一部署 | `docker compose up -d` |
| Windows 辅助脚本 | Windows 运维 | `scripts/windows/*.bat` |
| 模块化部署 | 拆分售前 / 运营 / 售后 | `python -m src.cli module ...` |

---

## 环境要求

### 通用

- Python 3.10+
- Node.js 18+
- npm
- Chrome / Edge（涉及 Cookie 获取与浏览器运行时）

### Docker

- Docker Engine 20.10+
- Docker Compose 2+

### 关键配置

- `XIANYU_COOKIE_1`
- `AI_PROVIDER / AI_API_KEY / AI_BASE_URL / AI_MODEL`
- `XGJ_APP_KEY / XGJ_APP_SECRET`（如需闲管家链路）

---

## 一、本地一键启动

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
cp .env.example .env

# macOS / Linux
./start.sh

# Windows
start.bat
```

脚本会自动：

1. 创建 `.env`（如果不存在）
2. 创建 Python 虚拟环境
3. 安装 Python 依赖
4. 安装 Playwright Chromium
5. 安装 Node.js 依赖
6. 启动三套服务：
   - React：5173
   - Node：3001
   - Python：8091

---

## 二、手动本地启动

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cd server && npm install && cd ..
cd client && npm install && cd ..
```

分别启动：

```bash
python -m src.dashboard_server --port 8091
npm run dev:server
npm run dev:client
```

健康检查：

```bash
curl http://localhost:8091/healthz
curl http://localhost:3001/health
```

---

## 三、Docker Compose 部署

```bash
cp .env.example .env
docker compose up -d
```

查看状态：

```bash
docker compose ps
docker compose logs -f
```

建议至少验证：

```bash
curl http://localhost:8091/healthz
curl http://localhost:3001/health
```

---

## 四、Windows 部署

### 1) 快速启动

```bat
start.bat
```

### 2) 常用脚本

```bat
scripts\windows\quickstart.bat
scripts\windows\doctor.bat
scripts\windows\module_check.bat
scripts\windows\module_status.bat
scripts\windows\module_logs.bat
scripts\windows\start_presales.bat
scripts\windows\start_operations.bat
scripts\windows\start_aftersales.bat
scripts\windows\quote_health.bat
scripts\windows\workflow_status.bat
scripts\windows\build_exe.bat
```

### 3) Windows EXE

仓库已包含 `src/windows_launcher.py` 与 `scripts/windows/build_exe.bat`，可用于构建图形化部署向导。

---

## 五、模块化部署

当前 CLI 已支持按模块拆分运行：

| 模块 | 说明 |
|------|------|
| `presales` | 售前消息、自动回复、工作流、报价 |
| `operations` | 擦亮、改价、指标任务 |
| `aftersales` | 售后订单跟进与回复 |

### 检查模块可用性

```bash
python -m src.cli module --action check --target all
```

### 查看模块状态

```bash
python -m src.cli module --action status --target all
```

### 启动模块

```bash
python -m src.cli module --action start --target presales --mode daemon --background
python -m src.cli module --action start --target operations --mode daemon --background
python -m src.cli module --action start --target aftersales --mode daemon --background
```

### 模块恢复 / 日志

```bash
python -m src.cli module --action recover --target presales
python -m src.cli module --action logs --target all --tail-lines 100
```

---

## 六、闲管家与订单回调

当前版本已支持：

- Dashboard 配置闲管家 AppKey / AppSecret
- 支付后自动触发订单同步
- 订单回调入口：`/api/orders/callback`
- API 改价 / API 发货手动重试

如果反向代理对外提供服务，需要确保该回调路径可被外部访问。

---

## 七、生产环境建议

### 1) 反向代理

你可以将：

- 前端代理到 `5173`
- Node API 代理到 `3001`
- Python Dashboard / API 代理到 `8091`

### 2) 守护与重启

- macOS：可用 `scripts/macos/install_service.sh`
- Windows：建议使用 bat 启动脚本 + 计划任务
- Linux：建议 systemd / supervisor / Docker restart policy

### 3) 备份

```bash
./scripts/backup_data.sh
```

---

## 八、升级流程

```bash
git pull origin main

# 本地
./start.sh

# Docker
docker compose down && docker compose up -d --build
```

如升级涉及依赖大版本变化，建议删除旧的 `.venv` 与 `node_modules` 后重装。

---

## 九、故障排查

### 1) 系统体检

```bash
python -m src.cli doctor --strict
```

### 2) Cookie 健康

```bash
python -m src.cli module --action cookie-health --target presales
```

### 3) 端口冲突

```bash
lsof -i :5173
lsof -i :3001
lsof -i :8091
```

### 4) 查看 Docker 日志

```bash
docker compose logs -f
```

---

## 十、相关文档

- [README.md](../README.md)
- [QUICKSTART.md](../QUICKSTART.md)
- [USER_GUIDE.md](../USER_GUIDE.md)
- [CHANGELOG.md](../CHANGELOG.md)

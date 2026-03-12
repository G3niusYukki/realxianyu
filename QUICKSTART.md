# 快速开始

这份文档面向希望 **尽快把项目跑起来** 的用户，默认以当前仓库结构为准。

---

## 1. 环境要求

- Python 3.10+
- Node.js 18+
- npm
- Chrome / Edge
- 一个可用的闲鱼 Cookie
- 一个可用的 AI API Key（如需自动回复）

---

## 2. 克隆仓库

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
```

---

## 3. 配置 `.env`

```bash
cp .env.example .env
```

最少建议填写：

```bash
XIANYU_COOKIE_1=your_cookie_here

AI_PROVIDER=deepseek
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

XGJ_APP_KEY=
XGJ_APP_SECRET=
```

---

## 4. 一键启动（推荐）

### macOS / Linux

```bash
./start.sh
```

### Windows

```bat
start.bat
```

脚本会自动完成：

- 创建 Python 虚拟环境
- 安装 Python 依赖
- 安装 Playwright Chromium
- 安装 Node.js 依赖
- 启动 Python / Node.js / React 三个服务

---

## 5. 访问地址

启动成功后访问：

| 服务 | 地址 |
|------|------|
| React 前端 | http://localhost:5173 |
| Python Dashboard | http://localhost:8091 |
| Node.js 健康检查 | http://localhost:3001/health |
| Python 健康检查 | http://localhost:8091/healthz |

---

## 6. 手动安装与启动（可选）

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cd server && npm install && cd ..
cd client && npm install && cd ..

python -m src.dashboard_server --port 8091
npm run dev:server
npm run dev:client
```

---

## 7. Docker 启动（可选）

```bash
cp .env.example .env
docker compose up -d
```

查看状态：

```bash
docker compose ps
docker compose logs -f
```

---

## 8. 启动后建议先做什么

1. 打开前端工作台，确认配置页面可访问
2. 检查 Cookie 是否有效
3. 配置 AI 服务
4. 如需用到闲管家，填写 AppKey / AppSecret
5. 运行一次系统诊断：

```bash
python -m src.cli doctor --strict
```

---

## 9. 常用排查命令

```bash
# 全局体检
python -m src.cli doctor --strict

# 模块状态
python -m src.cli module --action status --target all

# 查看日志
python -m src.cli module --action logs --target all --tail-lines 100

# Cookie 健康
python -m src.cli module --action cookie-health --target presales
```

---

## 10. 常见问题

### 端口占用

```bash
lsof -i :5173
lsof -i :3001
lsof -i :8091
```

### Playwright 安装失败

重新执行：

```bash
playwright install chromium
```

### Cookie 失效

重新登录闲鱼后更新 `XIANYU_COOKIE_1`，然后重启服务。

### Node / Python 依赖异常

```bash
rm -rf server/node_modules client/node_modules
rm -rf .venv
```

然后重新执行一键启动。

---

## 11. 下一步

- 完整说明：[README.md](README.md)
- 用户指南：[USER_GUIDE.md](USER_GUIDE.md)
- 部署文档：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 更新日志：[CHANGELOG.md](CHANGELOG.md)

# DEPLOYMENT

## 部署口径

当前推荐的完整部署形态：

- `React` 前端工作台
- `Python` 核心服务
- `Node` webhook / proxy

OpenClaw 不是默认路径，也不是必需依赖。

## 环境变量

根目录 `.env` 是当前唯一推荐配置入口。

必填：

```env
XIANYU_COOKIE_1=
AI_PROVIDER=
AI_API_KEY=
AI_BASE_URL=
AI_MODEL=
XGJ_APP_KEY=
XGJ_APP_SECRET=
XGJ_BASE_URL=https://open.goofish.pro
```

常用可选项：

```env
XGJ_MERCHANT_ID=
NODE_PORT=3001
PYTHON_PORT=8091
FRONTEND_PORT=5173
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite:///data/agent.db
```

## 本地部署

macOS / Linux：

```bash
cp .env.example .env
./start.sh
```

Windows：

```bat
copy .env.example .env
start.bat
```

默认端口：

- `5173` 前端
- `8091` Python
- `3001` Node

## 逐服务启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m src.dashboard_server --host 127.0.0.1 --port 8091

cd server && npm install && npm run dev
cd client && npm install && npm run dev
```

说明：

- 工作台主要依赖 Python。
- Node 负责 webhook 验签、闲管家透传和前端部分健康检查，完整部署建议一起启动。

## Docker Compose

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

Compose 服务：

- `react-frontend`
- `python-backend`
- `node-backend`

持久化：

- `./data`：SQLite、生成图、运行态数据
- `./config`：只读配置目录
- `node-data`：Node 侧少量运行时数据

## 健康检查

```bash
curl -fsS http://localhost:8091/healthz
curl -fsS http://localhost:3001/health
curl -fsS http://localhost:8091/api/config/sections
curl -fsS http://localhost:8091/api/accounts
```

如果前端已启动，再确认：

- 工作台首页能显示 `首次使用配置引导`
- 商品、订单、配置页面返回真实数据而不是占位样本

## 生产注意事项

- 配置以根目录 `.env` 和 Python 配置接口为准，不要再维护第二套配置真相源。
- `data/.encryption_key` 建议收紧权限：

```bash
chmod 600 data/.encryption_key
```

- 反向代理或网关部署时，优先保护 Python 和 Node 的管理接口，不要直接暴露未受控的 webhook 回调。
- 如果商品/订单异常，优先排查 Python 和闲管家配置，不要先查前端。

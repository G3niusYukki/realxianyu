# QUICKSTART

目标：在本机启动当前 `main` 的 API-first 闲鱼自动化工作台。

## 1. 准备环境

- Python `3.10+`
- Node.js `18+`
- 一个有效的闲鱼 Cookie
- 一个可用的 AI 提供商 Key
- 一个闲管家 Open Platform 应用

## 2. 复制配置模板

```bash
cp .env.example .env
```

最小必填项：

```env
XIANYU_COOKIE_1=

AI_PROVIDER=deepseek
AI_API_KEY=
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

XGJ_APP_KEY=
XGJ_APP_SECRET=
XGJ_BASE_URL=https://open.goofish.pro
```

## 3. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd server && npm install
cd ../client && npm install
cd ..
```

## 4. 启动

macOS / Linux：

```bash
./start.sh
```

Windows：

```bat
start.bat
```

也可以分别启动：

```bash
python3 -m src.dashboard_server --host 127.0.0.1 --port 8091
cd server && npm run dev
cd client && npm run dev
```

## 5. 访问地址

- 前端工作台：`http://127.0.0.1:5173`
- Python 核心：`http://127.0.0.1:8091`
- Node 薄代理：`http://127.0.0.1:3001`

## 6. 首次检查

先做健康检查：

```bash
curl -fsS http://127.0.0.1:8091/healthz
curl -fsS http://127.0.0.1:3001/health
curl -fsS http://127.0.0.1:8091/api/config/sections
curl -fsS http://127.0.0.1:8091/api/accounts
```

再在前端确认：

1. `工作台` 能显示系统状态和首次配置引导。
2. `店铺管理` 能识别 Cookie 和账号状态。
3. `系统配置` 能读写 AI / 闲管家配置。
4. `商品管理` 和 `订单中心` 能拉到真实数据。
5. `自动上架` 能生成真实预览图。

## 7. Docker 启动

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
```

默认端口映射：

- 前端 `5173`
- Python `8091`
- Node `3001`

## 8. 重要说明

- 当前主线不依赖 OpenClaw。
- React 页面全部接真实接口，不提供 mock 数据回退。
- Python 是唯一业务真相源；Node 只做代理、验签和 webhook 接入。
- `Legacy Browser Runtime` 只用于 API 暂时无法覆盖的补充链路。

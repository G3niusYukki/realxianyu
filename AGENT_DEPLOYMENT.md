# XianyuFlow | 闲流 - Agent Deployment Guide

> Verified against the local workspace on 2026-03-27.

This guide is for AI agents and automation tooling. It reflects the current repository state rather than older startup conventions.

## Runtime Facts

- Service entry: `python -m src.dashboard_server --host 127.0.0.1 --port 8091`
- Preflight-only entry: `python -m src.main`
- CLI entry: `python -m src.cli`
- Frontend output: `client/dist/`
- Health check: `GET /healthz`

`src.main` loads modules and exits successfully; it does not keep the Dashboard/API server running.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| npm | 9+ | Bundled with Node.js |
| SQLite | bundled | No external database needed |
| Chrome / Edge | optional | Useful for cookie extraction |
| DrissionPage runtime | optional | Used by Lite/browser automation flows |

## Quick Start

```bash
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu

python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd client
npm install
npm run build
cd ..

cp .env.example .env

python -m src.dashboard_server --host 127.0.0.1 --port 8091
```

Dashboard: `http://127.0.0.1:8091`

## Configuration

Copy `.env.example` to `.env` and fill the keys you actually need.

### Minimum practical variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `XIANYU_COOKIE_1` | Yes | Xianyu login cookie |
| `AI_PROVIDER` | Recommended | AI provider selection |
| `AI_API_KEY` | Recommended | AI auto-reply / content generation |
| `AI_BASE_URL` | Recommended | AI API base URL |
| `AI_MODEL` | Recommended | AI model name |
| `XGJ_APP_KEY` | Required for listing/orders | XianGuanjia app key |
| `XGJ_APP_SECRET` | Required for listing/orders | XianGuanjia app secret |

### Optional variables

- `COOKIE_CLOUD_UUID` / `COOKIE_CLOUD_PASSWORD`
- `APP_RUNTIME`
- `COOKIE_AUTO_REFRESH`
- `COOKIE_REFRESH_INTERVAL`
- `FRONTEND_PORT` for local Vite development only

### Configuration precedence

Runtime merges values in this order:

`config/config.yaml` < `data/system_config.json` < `.env` / shell environment

## Verification

After startup, validate the deployment with:

```bash
curl http://127.0.0.1:8091/healthz
python -m src.cli doctor --skip-quote
```

Expected:

- `/healthz` returns JSON with `"status": "ok"` or `"degraded"`
- `doctor` exits `0` in non-strict mode when critical checks pass

If you only want to confirm imports/modules before starting the long-running service:

```bash
python -m src.main
```

## Background Operation

### macOS launchd

```bash
bash scripts/install-launchd.sh
```

This installs a LaunchAgent that runs `src.dashboard_server`.

### Generic background process

```bash
nohup ./venv/bin/python -m src.dashboard_server --host 127.0.0.1 --port 8091 > logs/app.log 2>&1 &
echo $! > .pid
```

Stop:

```bash
kill "$(cat .pid)"
```

## Development Mode

Frontend dev proxy is optional and separate from production serving:

```bash
cd client
npm run dev
```

- Vite default port: `5173`
- Backend proxy target: `http://localhost:8091`
- Production deployment does not need port `5173`

## Quality Commands

```bash
./venv/bin/python -m pytest tests/ -q
```

`ruff` is not installed by `requirements.txt` alone. Install dev tooling first:

```bash
pip install -r requirements-dev.txt
./venv/bin/python -m ruff check src/
./venv/bin/python -m ruff format src/ --check
```

## Optional Infra Assets

The current local workspace also contains optional infra assets:

- `infra/terraform/main.tf`
- `infra/helm/xianyuflow-infra/values-kafka.yaml`
- `infra/helm/xianyuflow-infra/values-monitoring.yaml`

These are additive infrastructure building blocks for Kafka and monitoring. They are not required for single-machine deployment.

## Troubleshooting

### Port 8091 already in use

```bash
lsof -nP -iTCP:8091 -sTCP:LISTEN
```

If another process is already serving the Dashboard, reuse it or stop it explicitly before starting a new instance.

### `doctor` warns that port 5173 is not listening

That only means the Vite dev server is not running. It does not block normal deployment as long as `client/dist` exists and `src.dashboard_server` is serving `8091`.

### Dashboard loads but frontend is blank or 404s

Rebuild the frontend:

```bash
cd client && npm install && npm run build
```

### AI checks fail

The project can run without AI keys, but AI-powered replies will fall back to template behavior.

### Browser automation prerequisites

This repository now uses DrissionPage-based browser automation paths. Older Playwright-focused deployment notes are obsolete for the mainline runtime.

# Agent Documentation Index

> 当前仓库给 AI Agent 的快速事实表，已按 2026-03-27 本地实测更新。

## First Read

1. [../../AGENTS.md](../../AGENTS.md)
2. [../../CLAUDE.md](../../CLAUDE.md)
3. [../../AGENT_DEPLOYMENT.md](../../AGENT_DEPLOYMENT.md)
4. [../ARCHITECTURE.md](../ARCHITECTURE.md)

## Runtime Facts

- 主服务入口：`python -m src.dashboard_server --host 127.0.0.1 --port 8091`
- 预加载入口：`python -m src.main`
- CLI 入口：`python -m src.cli`
- 前端产物目录：`client/dist/`
- 健康检查：`/healthz`

## Quick Setup

```bash
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

## Configuration Order

`config/config.yaml` < `data/system_config.json` < `.env` / shell environment

## Required Project Constraints

- 不要把新业务逻辑加进 `src/dashboard/mimic_ops.py`
- 不要引入 `global` 状态
- 新配置优先进入 YAML 配置体系
- CLI 动态 import 模式要保留，便于 monkeypatch

## Verification

```bash
curl http://127.0.0.1:8091/healthz
python -m src.cli doctor --skip-quote
./venv/bin/python -m pytest tests/ -q
```

当前本地质量基线：

- `client`: `npm run build` 通过
- `pytest`: `1717 passed, 16 skipped`
- `doctor --skip-quote`: non-strict 通过

## Dev Tooling

`ruff` 不在 `requirements.txt` 中，需要额外安装：

```bash
pip install -r requirements-dev.txt
./venv/bin/python -m ruff check src/
./venv/bin/python -m ruff format src/ --check
```

## Dev Server Note

- `5173` 仅用于 `client` 目录下的 `npm run dev`
- 生产运行不依赖 5173
- `doctor` 对 5173 的告警不代表部署失败

## Useful Links

- [../../README.md](../../README.md)
- [../DEPLOYMENT.md](../DEPLOYMENT.md)
- [../API.md](../API.md)
- [../ARCHITECTURE.md](../ARCHITECTURE.md)

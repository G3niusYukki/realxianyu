- Xianyu operations automation toolkit: auto replies, smart quoting, order fulfillment, listing publish, and virtual goods verification.
- Stack: Python 3.12+ (`asyncio`) + React/Vite + SQLite.
- `src/modules/`: business modules such as `messages`, `orders`, `listing`, and `virtual_goods`.
- `src/integrations/`: XianGuanjia API integrations.
- `src/dashboard/`: dashboard routes, facade, and related services.
- `client/`: React/Vite frontend.
- `config/`: YAML-based configuration and rules.
- `tests/`: pytest suite.
- Use `CLAUDE.md` as the detailed repo source of truth when this file is not specific enough.
- Do not add new business logic to `src/dashboard/mimic_ops.py`; put logic in the appropriate module or service layer.
- Do not introduce `global` state; follow existing singleton patterns instead.
- Prefer the existing config system; add new config to YAML-backed config instead of creating a new source.
- Preserve existing import patterns, especially dynamic imports used by CLI code for test monkeypatching.
- YAML (`config/config.yaml`) is the main config source.
- Dashboard JSON (`data/system_config.json`) is UI override data.
- `.env` has the highest runtime priority.
- Do not add manual sync flows unless the repo already uses them.
```bash
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
python -m src.main
./venv/bin/python -m pytest tests/ -q
ruff check src/
ruff format src/
```
- Keep changes minimal and aligned with existing patterns.
- Run relevant tests before claiming completion when code behavior changes.
- Keep `pytest tests/ -q` passing for repo changes.
- Follow existing test naming conventions in `tests/`.

# 部署指南

> 基于本地工作区实测更新，最后验证日期：2026-04-01。

## 结论先说

- 真实服务入口是 `python -m src.dashboard_server --host 127.0.0.1 --port 8091`
- `python -m src.main` 只做模块预加载，不会常驻提供 Dashboard / API
- 前端生产产物是 `client/dist/`，由 `src.dashboard_server` 直接托管
- 单机部署不依赖 Docker、不依赖外部数据库

## 部署方式

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| 手动启动 | 本地 / 单机 | 最简单，适合首次部署 |
| nohup 守护 | Linux / macOS | 后台常驻运行 |
| launchd | macOS | 开机自启 |
| Helm / Terraform | 可选基础设施 | 当前工作区提供 Kafka / 监控补充样例 |

## 最小依赖

| 项目 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| npm | 9+ | 包管理 |
| SQLite | 内置 | 默认数据存储 |

## 单机部署流程

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

启动后访问：`http://127.0.0.1:8091`

## 启动前配置

### 必需项

- `XIANYU_COOKIE_1`

### 推荐项

- `AI_PROVIDER`
- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MODEL`

### 依业务而定

- `XGJ_APP_KEY`
- `XGJ_APP_SECRET`
- `COOKIE_CLOUD_UUID`
- `COOKIE_CLOUD_PASSWORD`

### 配置优先级

代码合并顺序为：

`config/config.yaml` < `data/system_config.json` < `.env` / shell 环境变量

## 部署后验证

```bash
curl http://127.0.0.1:8091/healthz
python -m src.cli doctor --skip-quote
```

当前本地验证结果：

- `client` 已成功 `npm run build`
- `/healthz` 返回正常 JSON
- `doctor --skip-quote` 非 strict 模式通过
- `pytest tests/ -q` 结果为 `1724 passed, 16 skipped`

## 后台运行

### nohup

```bash
nohup ./venv/bin/python -m src.dashboard_server --host 127.0.0.1 --port 8091 > logs/app.log 2>&1 &
echo $! > .pid
```

停止：

```bash
kill "$(cat .pid)"
```

### macOS LaunchAgent

```bash
bash scripts/install-launchd.sh
```

日志位于 `logs/launchd-stdout.log` 和 `logs/launchd-stderr.log`。

## 开发模式补充

如果你需要本地前端热更新：

```bash
cd client
npm run dev
```

- Vite 默认监听 `5173`
- 它只是开发代理，不是生产部署必需项
- `doctor` 中的 5173 警告不影响 `8091` 正常服务

## 可选基础设施

当前本地工作区多了 2 个仅本地领先远端的 infra 提交，新增内容如下：

- `infra/terraform/main.tf`
- `infra/helm/xianyuflow-infra/values-kafka.yaml`
- `infra/helm/xianyuflow-infra/values-monitoring.yaml`

这些文件用于补充 Kafka 和监控栈，不影响当前单机部署流程。

## 备份与升级

### 备份

```bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/ .env config/config.yaml
```

### 升级

```bash
git pull origin main
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
python -m src.dashboard_server --host 127.0.0.1 --port 8091
```

## 常见问题

### 8091 端口被占用

```bash
lsof -nP -iTCP:8091 -sTCP:LISTEN
```

### 页面空白或 404

通常是 `client/dist/` 不存在或过旧，重新执行前端构建：

```bash
cd client && npm install && npm run build
```

### `ruff` 命令找不到

`requirements.txt` 不包含 Ruff。需要先安装开发依赖：

```bash
pip install -r requirements-dev.txt
./venv/bin/python -m ruff check src/
./venv/bin/python -m ruff format src/ --check
```

### AI 未配置

服务仍可启动，但自动回复和内容生成功能会退化为模板模式。

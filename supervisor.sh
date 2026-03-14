#!/usr/bin/env bash
# 进程守护 —— 健康检查 + 自动重启
# 用法: ./supervisor.sh [--interval 15]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 配置 ──────────────────────────────────────
PYTHON_PORT=8091
VITE_PORT=5173
CHECK_INTERVAL="${1:-15}"        # 健康检查间隔（秒）
HEALTH_TIMEOUT=5                 # 单次健康检查超时（秒）
MAX_CONSECUTIVE_FAIL=2           # 连续失败几次后重启
LOG_FILE="logs/supervisor.log"

PYTHON_PID=""
VITE_PID=""

# ── 颜色 ──────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# ── 日志 ──────────────────────────────────────
mkdir -p logs
log() {
  local ts
  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  echo -e "${CYAN}[$ts]${NC} $1"
  echo "[$ts] $(echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g')" >> "$LOG_FILE"
}

# ── 清理 ──────────────────────────────────────
cleanup() {
  log "${YELLOW}正在停止所有服务...${NC}"
  [ -n "$PYTHON_PID" ] && kill "$PYTHON_PID" 2>/dev/null
  [ -n "$VITE_PID" ]   && kill "$VITE_PID"   2>/dev/null
  sleep 1
  [ -n "$PYTHON_PID" ] && kill -9 "$PYTHON_PID" 2>/dev/null
  [ -n "$VITE_PID" ]   && kill -9 "$VITE_PID"   2>/dev/null
  wait 2>/dev/null
  log "${GREEN}所有服务已停止${NC}"
  exit 0
}
trap cleanup EXIT INT TERM

# ── 启动函数 ──────────────────────────────────
start_python() {
  # 先清理残留
  local old_pid
  old_pid="$(lsof -ti :$PYTHON_PORT 2>/dev/null || true)"
  if [ -n "$old_pid" ]; then
    kill "$old_pid" 2>/dev/null; sleep 1; kill -9 "$old_pid" 2>/dev/null
  fi
  log "${GREEN}启动 Python 后端 (端口 $PYTHON_PORT)...${NC}"
  python3 -m src.dashboard_server --port "$PYTHON_PORT" &
  PYTHON_PID=$!
  PYTHON_FAIL_COUNT=0
}

start_vite() {
  local old_pid
  old_pid="$(lsof -ti :$VITE_PORT 2>/dev/null || true)"
  if [ -n "$old_pid" ]; then
    kill "$old_pid" 2>/dev/null; sleep 1; kill -9 "$old_pid" 2>/dev/null
  fi
  log "${GREEN}启动 Vite 前端 (端口 $VITE_PORT)...${NC}"
  (cd client && npx vite --host) &
  VITE_PID=$!
  VITE_FAIL_COUNT=0
}

# ── 健康检查（HTTP 级别，不只是进程是否存在） ──
check_http() {
  local port=$1 path=$2
  curl -sf --max-time "$HEALTH_TIMEOUT" "http://localhost:${port}${path}" >/dev/null 2>&1
}

check_process() {
  local pid=$1
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

# ── 主流程 ────────────────────────────────────
echo ""
echo "========================================="
echo "  闲鱼管家 - 进程守护模式"
echo "  健康检查间隔: ${CHECK_INTERVAL}s"
echo "========================================="
echo ""

PYTHON_FAIL_COUNT=0
VITE_FAIL_COUNT=0

start_python
sleep 2
start_vite
sleep 2

log "${GREEN}所有服务已启动${NC}"
log "管理面板:    http://localhost:$VITE_PORT"
log "Python 后端: http://localhost:$PYTHON_PORT"
log ""
log "守护进程运行中，按 ${YELLOW}Ctrl+C${NC} 停止"

while true; do
  sleep "$CHECK_INTERVAL"

  # ── Python 后端检查 ──
  if ! check_process "$PYTHON_PID"; then
    log "${RED}[Python] 进程已退出，立即重启${NC}"
    start_python
    sleep 3
  elif ! check_http "$PYTHON_PORT" "/api/config"; then
    PYTHON_FAIL_COUNT=$((PYTHON_FAIL_COUNT + 1))
    log "${YELLOW}[Python] 健康检查失败 ($PYTHON_FAIL_COUNT/$MAX_CONSECUTIVE_FAIL)${NC}"
    if [ "$PYTHON_FAIL_COUNT" -ge "$MAX_CONSECUTIVE_FAIL" ]; then
      log "${RED}[Python] 连续 $MAX_CONSECUTIVE_FAIL 次无响应，强制重启${NC}"
      kill "$PYTHON_PID" 2>/dev/null; sleep 1; kill -9 "$PYTHON_PID" 2>/dev/null
      start_python
      sleep 3
    fi
  else
    if [ "$PYTHON_FAIL_COUNT" -gt 0 ]; then
      log "${GREEN}[Python] 已恢复正常${NC}"
    fi
    PYTHON_FAIL_COUNT=0
  fi

  # ── Vite 前端检查 ──
  if ! check_process "$VITE_PID"; then
    log "${RED}[Vite] 进程已退出，立即重启${NC}"
    start_vite
    sleep 2
  elif ! check_http "$VITE_PORT" "/"; then
    VITE_FAIL_COUNT=$((VITE_FAIL_COUNT + 1))
    log "${YELLOW}[Vite] 健康检查失败 ($VITE_FAIL_COUNT/$MAX_CONSECUTIVE_FAIL)${NC}"
    if [ "$VITE_FAIL_COUNT" -ge "$MAX_CONSECUTIVE_FAIL" ]; then
      log "${RED}[Vite] 连续 $MAX_CONSECUTIVE_FAIL 次无响应，强制重启${NC}"
      kill "$VITE_PID" 2>/dev/null; sleep 1; kill -9 "$VITE_PID" 2>/dev/null
      start_vite
      sleep 2
    fi
  else
    if [ "$VITE_FAIL_COUNT" -gt 0 ]; then
      log "${GREEN}[Vite] 已恢复正常${NC}"
    fi
    VITE_FAIL_COUNT=0
  fi
done

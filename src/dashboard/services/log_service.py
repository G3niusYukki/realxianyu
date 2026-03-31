"""Dashboard log file service — log reading, risk control detection, message stats."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.core.config import get_config

logger = logging.getLogger(__name__)

_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_LOG_TIME_RE = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})")

_RISK_BLOCK_PATTERNS = (
    "fail_sys_user_validate",
    "rgv587",
    "账号异常",
    "账号风险",
    "安全验证",
    "访问受限",
    "封控",
    "封禁",
)
_RISK_WARN_PATTERNS = (
    "http 400",
    "http 403",
    "forbidden",
    "unauthorized",
    "token api failed",
    "需要验证码",
    "验证码",
    "校验失败",
)
_RISK_SIGNAL_WINDOW_MINUTES = 120


class LogService:
    """Handles log file listing, reading, risk control detection, and message stats."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.logs_dir = project_root / "logs"
        self._risk_log_cache: dict[str, Any] | None = None
        self._risk_log_cache_ts: float = 0.0

    # ── properties ──────────────────────────────────────────────────

    @property
    def _RISK_BLOCK_PATTERNS(self) -> tuple[str, ...]:
        return _RISK_BLOCK_PATTERNS

    @property
    def _RISK_WARN_PATTERNS(self) -> tuple[str, ...]:
        return _RISK_WARN_PATTERNS

    @property
    def _RISK_SIGNAL_WINDOW_MINUTES(self) -> int:
        return _RISK_SIGNAL_WINDOW_MINUTES

    # ── helpers ─────────────────────────────────────────────────────

    def _module_runtime_log(self, target: str) -> Path:
        return self.project_root / "data" / "module_runtime" / f"{target}.log"

    def _workflow_db_path(self) -> Path:
        messages_cfg = get_config().get_section("messages", {})
        workflow_cfg = messages_cfg.get("workflow", {}) if isinstance(messages_cfg.get("workflow"), dict) else {}
        raw = str(workflow_cfg.get("db_path", "data/workflow.db") or "data/workflow.db")
        path = Path(raw)
        if not path.is_absolute():
            path = self.project_root / path
        return path

    @classmethod
    def _strip_ansi(cls, text: str) -> str:
        return _ANSI_ESCAPE_RE.sub("", str(text or "")).strip()

    @classmethod
    def _extract_log_time(cls, text: str) -> str:
        cleaned = cls._strip_ansi(text)
        m = _LOG_TIME_RE.search(cleaned)
        return str(m.group(1)) if m else ""

    @classmethod
    def _parse_log_datetime(cls, text: str) -> datetime | None:
        ts_str = cls._extract_log_time(text)
        if not ts_str:
            return None
        try:
            return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    # ── log file listing & reading ──────────────────────────────────

    def list_log_files(self) -> dict[str, Any]:
        files: list[dict[str, Any]] = []
        runtime_dir = self.project_root / "data" / "module_runtime"
        conversations_dir = self.logs_dir / "conversations"

        for fp in runtime_dir.glob("*.log"):
            if not fp.is_file():
                continue
            stat = fp.stat()
            files.append(
                {
                    "name": f"runtime/{fp.name}",
                    "path": str(fp),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "runtime",
                }
            )

        for fp in self.logs_dir.glob("*.log"):
            if not fp.is_file():
                continue
            stat = fp.stat()
            files.append(
                {
                    "name": f"app/{fp.name}",
                    "path": str(fp),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "app",
                }
            )

        for fp in conversations_dir.glob("*.log"):
            if not fp.is_file():
                continue
            stat = fp.stat()
            files.append(
                {
                    "name": f"conversations/{fp.name}",
                    "path": str(fp),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": "conversation",
                }
            )

        files.sort(key=lambda x: str(x.get("modified", "")), reverse=True)
        return {"success": True, "files": files}

    def _resolve_log_file(self, file_name: str) -> Path:
        name = str(file_name or "").strip()
        if name in {"presales", "operations", "aftersales"}:
            return self._module_runtime_log(name)
        if name == "app":
            app_logs = sorted(
                (p for p in self.logs_dir.glob("app_*.log") if p.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if app_logs:
                return app_logs[0]
            return self.logs_dir / "app.log"
        if name.startswith("runtime/"):
            return self.project_root / "data" / "module_runtime" / name.replace("runtime/", "", 1)
        if name.startswith("app/"):
            return self.logs_dir / name.replace("app/", "", 1)
        if name.startswith("conversations/"):
            return self.logs_dir / "conversations" / name.replace("conversations/", "", 1)

        safe_name = Path(name).name
        app_path = self.logs_dir / safe_name
        if app_path.exists():
            return app_path
        return self.project_root / "data" / "module_runtime" / safe_name

    def read_log_content(
        self,
        file_name: str,
        tail: int = 200,
        page: int | None = None,
        size: int | None = None,
        search: str = "",
    ) -> dict[str, Any]:
        name = str(file_name or "").strip()
        if not name:
            return {"success": False, "error": "file is required"}

        fp = self._resolve_log_file(name)

        if not fp.exists():
            return {"success": False, "error": "log file not found", "file": str(fp)}

        lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()

        search_text = str(search or "").strip().lower()
        if search_text:
            lines = [line for line in lines if search_text in line.lower()]

        if page is not None or size is not None:
            page_n = max(1, int(page or 1))
            page_size = max(10, min(int(size or 100), 2000))
            total_lines = len(lines)
            total_pages = (total_lines + page_size - 1) // page_size if total_lines > 0 else 1
            if page_n > total_pages:
                page_n = total_pages
            start = (page_n - 1) * page_size
            end = start + page_size
            return {
                "success": True,
                "file": str(fp),
                "lines": lines[start:end],
                "total_lines": total_lines,
                "page": page_n,
                "total_pages": total_pages,
                "page_size": page_size,
                "search": search_text,
            }

        tail_n = max(1, min(int(tail), 5000))
        return {"success": True, "file": str(fp), "lines": lines[-tail_n:], "total_lines": len(lines)}

    # ── unmatched message stats ─────────────────────────────────────

    def get_unmatched_message_stats(self, max_lines: int = 3000, top_n: int = 10) -> dict[str, Any]:
        """统计 data/unmatched_messages.jsonl 的高频词与趋势。"""
        from collections import Counter

        path = self.project_root / "data" / "unmatched_messages.jsonl"
        if not path.exists():
            return {
                "ok": True,
                "total_count": 0,
                "top_keywords": [],
                "daily_counts": [],
            }
        lines: list[str] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    lines.append(line)
                    if len(lines) > max_lines:
                        lines.pop(0)
        except Exception as exc:
            logger.warning("unmatched_messages read failed: %s", exc)
            return {"ok": False, "error": str(exc), "total_count": 0, "top_keywords": [], "daily_counts": []}
        total = len(lines)
        msgs: list[str] = []
        daily: dict[str, int] = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                msg = (obj.get("msg") or "").strip()
                if msg:
                    msgs.append(msg)
                ts = obj.get("ts", "")
                if ts:
                    day = ts[:10]
                    daily[day] = daily.get(day, 0) + 1
            except Exception:
                continue
        counter: Counter[str] = Counter()
        for msg in msgs:
            for seg in re.findall(r"[\u4e00-\u9fa5]{2,4}", msg):
                if len(seg) >= 2:
                    counter[seg] += 1
            for part in re.split(r"[，。！？、；：\s]+", msg):
                part = part.strip()
                if part and len(part) >= 2 and not part.isdigit():
                    counter[part] += 1
        top_keywords = [{"word": w, "count": c} for w, c in counter.most_common(top_n)]
        daily_counts = [{"date": d, "count": daily[d]} for d in sorted(daily.keys(), reverse=True)[:14]]
        return {
            "ok": True,
            "total_count": total,
            "top_keywords": top_keywords,
            "daily_counts": daily_counts,
        }

    # ── workflow message stats ──────────────────────────────────────

    def _query_message_stats_from_workflow(self) -> dict[str, Any] | None:
        db_path = self._workflow_db_path()
        if not db_path.exists():
            return None

        reply_states = ("REPLIED", "QUOTED")
        ok_status = ("success", "forced")
        try:
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")

                total_replied = int(
                    conn.execute(
                        """
                        SELECT COUNT(DISTINCT session_id) AS c
                        FROM session_state_transitions
                        WHERE status IN (?, ?)
                          AND to_state IN (?, ?)
                        """,
                        (ok_status[0], ok_status[1], reply_states[0], reply_states[1]),
                    ).fetchone()["c"]
                )

                today_replied = int(
                    conn.execute(
                        """
                        SELECT COUNT(DISTINCT session_id) AS c
                        FROM session_state_transitions
                        WHERE status IN (?, ?)
                          AND to_state IN (?, ?)
                          AND date(datetime(created_at), 'localtime') = date('now', 'localtime')
                          AND session_id IN (
                              SELECT session_id FROM session_tasks
                              WHERE date(datetime(created_at), 'localtime') = date('now', 'localtime')
                          )
                        """,
                        (ok_status[0], ok_status[1], reply_states[0], reply_states[1]),
                    ).fetchone()["c"]
                )

                recent_replied = int(
                    conn.execute(
                        """
                        SELECT COUNT(DISTINCT session_id) AS c
                        FROM session_state_transitions
                        WHERE status IN (?, ?)
                          AND to_state IN (?, ?)
                          AND datetime(created_at) >= datetime('now', '-60 minutes')
                        """,
                        (ok_status[0], ok_status[1], reply_states[0], reply_states[1]),
                    ).fetchone()["c"]
                )

                total_conversations = int(conn.execute("SELECT COUNT(*) AS c FROM session_tasks").fetchone()["c"])
                today_conversations = int(
                    conn.execute(
                        """SELECT COUNT(*) AS c FROM session_tasks
                           WHERE date(datetime(created_at), 'localtime') = date('now', 'localtime')""",
                    ).fetchone()["c"]
                )
                total_messages = int(conn.execute("SELECT COUNT(*) AS c FROM workflow_jobs").fetchone()["c"])

                hourly_rows = conn.execute(
                    """
                    SELECT strftime('%H', datetime(created_at), 'localtime') AS h, COUNT(*) AS c
                    FROM session_state_transitions
                    WHERE status IN (?, ?)
                      AND to_state IN (?, ?)
                      AND datetime(created_at) >= datetime('now', '-24 hours')
                    GROUP BY h
                    """,
                    (ok_status[0], ok_status[1], reply_states[0], reply_states[1]),
                ).fetchall()

                daily_rows = conn.execute(
                    """
                    SELECT strftime('%Y-%m-%d', datetime(created_at), 'localtime') AS d, COUNT(*) AS c
                    FROM session_state_transitions
                    WHERE status IN (?, ?)
                      AND to_state IN (?, ?)
                      AND date(datetime(created_at), 'localtime') >= date('now', 'localtime', '-6 days')
                    GROUP BY d
                    """,
                    (ok_status[0], ok_status[1], reply_states[0], reply_states[1]),
                ).fetchall()

            hourly = {str(r["h"]): int(r["c"]) for r in hourly_rows if r["h"] is not None}
            daily = {str(r["d"]): int(r["c"]) for r in daily_rows if r["d"] is not None}
            return {
                "total_replied": total_replied,
                "today_replied": today_replied,
                "recent_replied": recent_replied,
                "total_conversations": total_conversations,
                "today_conversations": today_conversations,
                "total_messages": total_messages,
                "hourly_replies": hourly,
                "daily_replies": daily,
            }
        except Exception:
            return None

    # ── risk control from logs ──────────────────────────────────────

    _RISK_LOG_CACHE_TTL: float = 5.0

    def _risk_control_status_from_logs(self, target: str = "presales", tail_lines: int = 300) -> dict[str, Any]:
        now = time.time()
        if self._risk_log_cache is not None and (now - self._risk_log_cache_ts) < self._RISK_LOG_CACHE_TTL:
            return self._risk_log_cache

        result = self._risk_control_status_from_logs_uncached(target=target, tail_lines=tail_lines)
        self._risk_log_cache = result
        self._risk_log_cache_ts = now
        return result

    def _risk_control_status_from_logs_uncached(
        self, target: str = "presales", tail_lines: int = 300
    ) -> dict[str, Any]:
        from src.dashboard.helpers.utils import _now_iso

        fp = self._module_runtime_log(target)
        empty = {
            "last_event": "",
            "last_event_at": "",
            "checked_lines": 0,
            "source_log": str(fp),
            "updated_at": _now_iso(),
        }
        if not fp.exists():
            return {
                "level": "unknown",
                "label": "未检测（无日志）",
                "score": 0,
                "signals": ["日志文件不存在"],
                **empty,
            }

        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            return {
                "level": "unknown",
                "label": "未检测（读取失败）",
                "score": 0,
                "signals": [f"日志读取失败: {e}"],
                **empty,
            }

        tail_n = max(50, min(int(tail_lines or 300), 2000))
        recent = [self._strip_ansi(line) for line in lines[-tail_n:] if str(line or "").strip()]
        if not recent:
            return {"level": "unknown", "label": "未检测（空日志）", "score": 0, "signals": ["日志内容为空"], **empty}

        block_hits: list[tuple[int, str]] = []
        warn_hits: list[tuple[int, str]] = []
        ws_400_lines: list[tuple[int, str]] = []
        connected_hits: list[tuple[int, str]] = []

        RECOVERY_SKIP = ("succeeded", "成功", "已恢复", "已过期")

        for idx, line in enumerate(recent):
            lowered = line.lower()
            if "connected to goofish websocket transport" in lowered:
                connected_hits.append((idx, line))
            if any(token in lowered for token in _RISK_BLOCK_PATTERNS):
                if not any(skip in lowered for skip in RECOVERY_SKIP):
                    block_hits.append((idx, line))
                continue
            if any(token in lowered for token in _RISK_WARN_PATTERNS):
                warn_hits.append((idx, line))
            if "websocket" in lowered and "http 400" in lowered:
                ws_400_lines.append((idx, line))

        now = datetime.now()
        window = timedelta(minutes=_RISK_SIGNAL_WINDOW_MINUTES)

        def _split_by_freshness(
            hits: list[tuple[int, str]],
        ) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
            active, stale = [], []
            for idx, line in hits:
                ts = self._parse_log_datetime(line)
                if ts is None:
                    stale.append((idx, line))
                elif (now - ts) > window:
                    stale.append((idx, line))
                else:
                    active.append((idx, line))
            return active, stale

        active_blocks, stale_blocks = _split_by_freshness(block_hits)
        active_warns, stale_warns = _split_by_freshness(warn_hits)
        active_ws400, stale_ws400 = _split_by_freshness(ws_400_lines)

        level = "normal"
        label = "正常"
        score = 0
        signals: list[str] = ["未发现封控信号"]
        last_event = recent[-1]

        if active_blocks:
            level = "blocked"
            label = "疑似封控"
            score = min(100, 75 + len(active_blocks) * 4)
            signals = [f"高风险信号 x{len(active_blocks)}"]
            if active_ws400:
                signals.append(f"WebSocket HTTP 400 x{len(active_ws400)}")
            last_event = active_blocks[-1][1]
        elif stale_blocks and not active_blocks:
            last_block_time = self._extract_log_time(stale_blocks[-1][1])
            level = "normal"
            label = "正常"
            score = 0
            signals = [
                (
                    f"历史高风险信号 x{len(stale_blocks)}"
                    f"（最后于 {last_block_time}，"
                    f"已超过 {_RISK_SIGNAL_WINDOW_MINUTES} 分钟，已过期）"
                )
            ]
            last_event = stale_blocks[-1][1]
        elif len(active_ws400) >= 10 or active_warns:
            level = "warning"
            label = "风险预警"
            score = min(85, 30 + len(active_warns) * 4 + len(active_ws400) * 2)
            signals = []
            if active_ws400:
                signals.append(f"WebSocket HTTP 400 x{len(active_ws400)}")
            if active_warns:
                signals.append(f"异常告警 x{len(active_warns)}")
            last_event = (active_warns or active_ws400)[-1][1]
        elif stale_warns or stale_ws400:
            stale_total = len(stale_warns) + len(stale_ws400)
            last_stale = stale_warns[-1] if stale_warns else stale_ws400[-1]
            last_stale_time = self._extract_log_time(last_stale[1])
            level = "normal"
            label = "正常"
            score = 0
            signals = [
                (
                    f"历史异常信号 x{stale_total}"
                    f"（最后于 {last_stale_time}，"
                    f"已超过 {_RISK_SIGNAL_WINDOW_MINUTES} 分钟，已过期）"
                )
            ]
            last_event = last_stale[1]

        last_connected_at = ""
        if connected_hits:
            last_connected_line = connected_hits[-1][1]
            last_connected_idx = connected_hits[-1][0]
            last_connected_at = self._extract_log_time(last_connected_line)
            last_risk_idx = -1
            if active_blocks:
                last_risk_idx = max(last_risk_idx, active_blocks[-1][0])
            if active_warns:
                last_risk_idx = max(last_risk_idx, active_warns[-1][0])
            if active_ws400:
                last_risk_idx = max(last_risk_idx, active_ws400[-1][0])
            if last_connected_idx > last_risk_idx >= 0:
                level = "normal"
                label = "已恢复连接"
                score = 0
                signals = ["最近已恢复连接"]
                last_event = last_connected_line

        return {
            "level": level,
            "label": label,
            "score": int(score),
            "signals": signals,
            "last_event": str(last_event)[-180:],
            "last_event_at": self._extract_log_time(last_event),
            "last_connected_at": last_connected_at,
            "checked_lines": len(recent),
            "source_log": str(fp),
            "updated_at": _now_iso(),
        }

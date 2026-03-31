"""Dashboard template service — reply templates and reply logs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_WEIGHT_TEMPLATE = (
    "{origin_province}到{dest_province} {billing_weight}kg 参考价格\n"
    "{courier}: {price} 元\n"
    "预计时效：{eta_days}\n"
    "重要提示：\n"
    "体积重大于实际重量时按体积计费！"
)
DEFAULT_VOLUME_TEMPLATE = (
    "{origin_province}到{dest_province} {billing_weight}kg 参考价格\n"
    "体积重规则：{volume_formula}\n"
    "{courier}: {price} 元\n"
    "预计时效：{eta_days}\n"
    "重要提示：\n"
    "体积重大于实际重量时按体积计费！"
)


from src.dashboard.helpers.utils import _now_iso


class TemplateService:
    """Handles reply template CRUD and reply log queries."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    @property
    def template_path(self) -> Path:
        return self.project_root / "config" / "templates" / "reply_templates.json"

    def get_template(self, default: bool = False) -> dict[str, Any]:
        if default:
            return {
                "success": True,
                "weight_template": DEFAULT_WEIGHT_TEMPLATE,
                "volume_template": DEFAULT_VOLUME_TEMPLATE,
            }
        if self.template_path.exists():
            try:
                data = json.loads(self.template_path.read_text(encoding="utf-8"))
                return {
                    "success": True,
                    "weight_template": str(data.get("weight_template") or DEFAULT_WEIGHT_TEMPLATE),
                    "volume_template": str(data.get("volume_template") or DEFAULT_VOLUME_TEMPLATE),
                }
            except Exception:
                pass
        return {
            "success": True,
            "weight_template": DEFAULT_WEIGHT_TEMPLATE,
            "volume_template": DEFAULT_VOLUME_TEMPLATE,
        }

    def save_template(self, weight_template: str, volume_template: str) -> dict[str, Any]:
        payload = {
            "weight_template": str(weight_template or DEFAULT_WEIGHT_TEMPLATE).strip() or DEFAULT_WEIGHT_TEMPLATE,
            "volume_template": str(volume_template or DEFAULT_VOLUME_TEMPLATE).strip() or DEFAULT_VOLUME_TEMPLATE,
            "updated_at": _now_iso(),
        }
        self.template_path.parent.mkdir(parents=True, exist_ok=True)
        self.template_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"success": True, "message": "Template saved", **payload}

    def get_replies(self) -> list[dict[str, Any]]:
        """查询自动回复日志（关联 workflow_jobs + compliance_audit 补充缺失数据）。"""
        db = self.project_root / "data" / "workflow.db"
        if not db.exists():
            return []
        try:
            conn = sqlite3.connect(str(db))
            conn.row_factory = sqlite3.Row

            comp_db = self.project_root / "data" / "compliance.db"
            has_comp = comp_db.exists()
            if has_comp:
                conn.execute("ATTACH DATABASE ? AS comp", (str(comp_db),))

            rows = conn.execute(
                """SELECT id, session_id, to_state, metadata, created_at
                   FROM session_state_transitions
                   WHERE to_state IN ('REPLIED','QUOTED') AND status='success'
                   ORDER BY created_at DESC LIMIT 200"""
            ).fetchall()

            sids = list({r["session_id"] for r in rows})

            job_map: dict[str, dict] = {}
            if sids:
                ph = ",".join("?" * len(sids))
                for jr in conn.execute(
                    f"SELECT session_id, payload_json FROM workflow_jobs"
                    f" WHERE session_id IN ({ph}) AND stage='reply' ORDER BY id DESC",
                    sids,
                ):
                    if jr["session_id"] not in job_map:
                        job_map[jr["session_id"]] = json.loads(jr["payload_json"]) if jr["payload_json"] else {}

            audit_map: dict[str, str] = {}
            if has_comp and sids:
                ph = ",".join("?" * len(sids))
                for ar in conn.execute(
                    f"SELECT session_id, content FROM comp.compliance_audit"
                    f" WHERE session_id IN ({ph}) AND action='message_send' AND blocked=0"
                    f" ORDER BY created_at DESC",
                    sids,
                ):
                    if ar["session_id"] not in audit_map:
                        audit_map[ar["session_id"]] = ar["content"]

            conn.close()
        except Exception:
            return []

        logs: list[dict[str, Any]] = []
        for r in rows:
            meta = json.loads(r["metadata"]) if r["metadata"] else {}
            payload = job_map.get(r["session_id"], {})
            logs.append(
                {
                    "id": str(r["id"]),
                    "session_id": r["session_id"],
                    "buyer_message": meta.get("buyer_message") or payload.get("last_message", ""),
                    "reply_text": meta.get("reply_text") or audit_map.get(r["session_id"], ""),
                    "intent": "quote" if meta.get("quote") else meta.get("intent", "auto_reply"),
                    "item_title": meta.get("peer_name") or payload.get("peer_name", ""),
                    "replied_at": r["created_at"],
                }
            )
        return logs

    def get_reply_templates(self) -> dict[str, Any]:
        """返回回复模板配置（原 get_replies 功能）。"""
        template = self.get_template(default=False)
        return {
            "success": bool(template.get("success")),
            "replies": {
                "weight_template": str(template.get("weight_template") or DEFAULT_WEIGHT_TEMPLATE),
                "volume_template": str(template.get("volume_template") or DEFAULT_VOLUME_TEMPLATE),
            },
            "updated_at": str(template.get("updated_at") or ""),
        }

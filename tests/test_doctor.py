"""doctor 自检报告测试。"""

import json

import src.core.doctor as doctor
import src.core.startup_checks as startup_checks
from src.core.doctor import run_doctor
from src.core.startup_checks import StartupCheckResult


def test_doctor_report_not_ready_when_critical_check_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.core.doctor.run_all_checks",
        lambda skip_browser=False: [  # noqa: ARG005
            StartupCheckResult("Lite 浏览器驱动", False, "未安装 DrissionPage", critical=True),
        ],
    )
    monkeypatch.setattr("src.core.doctor._extra_checks", lambda skip_quote=False: [])  # noqa: ARG005

    report = run_doctor(skip_quote=True)

    assert report["ready"] is False
    assert report["summary"]["critical_failed"] == 1
    assert any("DrissionPage" in step or "pip install" in step for step in report["next_steps"])


def test_doctor_report_ready_with_warning_only(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.core.doctor.run_all_checks",
        lambda skip_browser=False: [  # noqa: ARG005
            StartupCheckResult("Python版本", True, "ok", critical=True),
        ],
    )
    monkeypatch.setattr(
        "src.core.doctor._extra_checks",
        lambda skip_quote=False: [  # noqa: ARG005
            {
                "name": "AI服务",
                "passed": False,
                "critical": False,
                "message": "未配置",
                "suggestion": "配置 API Key",
                "meta": {},
            }
        ],
    )

    report = run_doctor(skip_quote=True)

    assert report["ready"] is True
    assert report["summary"]["critical_failed"] == 0
    assert report["summary"]["warning_failed"] == 1
    assert report["next_steps"] == ["配置 API Key"]


def test_extra_checks_contains_dashboard_daemon_status(monkeypatch) -> None:
    class _Cfg:
        @staticmethod
        def get_section(name: str, default=None):
            if name == "messages":
                return {"fast_reply_enabled": True, "reply_target_seconds": 3.0}
            return default if default is not None else {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        def read(self) -> bytes:
            return json.dumps({"service_status": "running"}).encode("utf-8")

    monkeypatch.setattr(doctor, "get_config", lambda: _Cfg())
    monkeypatch.setattr(doctor, "_check_port_open", lambda port, host="127.0.0.1", timeout=0.3: True)  # noqa: ARG005
    monkeypatch.setattr(doctor.urllib.request, "urlopen", lambda *args, **kwargs: _Resp())

    checks = doctor._extra_checks(skip_quote=True)
    dashboard_check = next(item for item in checks if item["name"] == "Dashboard守护状态")

    assert dashboard_check["passed"] is True
    assert "Dashboard API 正常" in dashboard_check["message"]


def test_extra_checks_dashboard_daemon_status_failed_when_port_closed(monkeypatch) -> None:
    class _Cfg:
        @staticmethod
        def get_section(name: str, default=None):
            if name == "messages":
                return {"fast_reply_enabled": True, "reply_target_seconds": 3.0}
            return default if default is not None else {}

    monkeypatch.setattr(doctor, "get_config", lambda: _Cfg())
    monkeypatch.setattr(
        doctor,
        "_check_port_open",
        lambda port, host="127.0.0.1", timeout=0.3: False,  # noqa: ARG005
    )

    checks = doctor._extra_checks(skip_quote=True)
    dashboard_check = next(item for item in checks if item["name"] == "Dashboard守护状态")

    assert dashboard_check["passed"] is False
    assert "端口未监听" in dashboard_check["message"]


def test_extra_checks_web_ui_port_suggestion_mentions_vite_dev_only(monkeypatch) -> None:
    class _Cfg:
        @staticmethod
        def get_section(name: str, default=None):
            if name == "messages":
                return {"fast_reply_enabled": True, "reply_target_seconds": 3.0}
            return default if default is not None else {}

    def _check_port_open(port, host="127.0.0.1", timeout=0.3):  # noqa: ARG001
        return port == 8091

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        def read(self) -> bytes:
            return json.dumps({"service_status": "running"}).encode("utf-8")

    monkeypatch.setattr(doctor, "get_config", lambda: _Cfg())
    monkeypatch.setattr(doctor, "_check_port_open", _check_port_open)
    monkeypatch.setattr(doctor.urllib.request, "urlopen", lambda *args, **kwargs: _Resp())
    monkeypatch.setattr(startup_checks, "resolve_runtime_mode", lambda: "auto")

    checks = doctor._extra_checks(skip_quote=True)
    web_ui_check = next(item for item in checks if item["name"] == "Web UI 端口")

    # passed depends on whether port 5173 is actually open in the environment.
    # What matters is that the suggestion correctly documents the dev-only nature.
    assert "npm run dev" in web_ui_check["suggestion"]
    assert "生产部署无需监听 5173" in web_ui_check["suggestion"]

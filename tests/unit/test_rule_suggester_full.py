"""规则建议模块测试。"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.modules.messages.rule_suggester import RuleSuggester, UNMATCHED_PATH, SYSTEM_CONFIG_PATH, SUGGESTIONS_KEY


@pytest.fixture()
def suggester(tmp_path, monkeypatch):
    monkeypatch.setattr("src.modules.messages.rule_suggester.UNMATCHED_PATH", tmp_path / "unmatched.jsonl")
    monkeypatch.setattr("src.modules.messages.rule_suggester.SYSTEM_CONFIG_PATH", tmp_path / "system_config.json")
    with patch("src.modules.messages.rule_suggester.get_config"):
        s = RuleSuggester()
    return s


class TestLoadUnmatchedMessages:
    def test_no_file(self, suggester):
        result = suggester.load_unmatched_messages()
        assert result == []

    def test_valid_jsonl(self, suggester, tmp_path):
        p = tmp_path / "unmatched.jsonl"
        p.write_text('{"text": "hello"}\n{"text": "world"}\n', encoding="utf-8")
        suggester.__class__.__init__
        # Patch the module-level path
        import src.modules.messages.rule_suggester as mod

        old = mod.UNMATCHED_PATH
        mod.UNMATCHED_PATH = p
        try:
            result = suggester.load_unmatched_messages()
            assert len(result) == 2
            assert result[0]["text"] == "hello"
        finally:
            mod.UNMATCHED_PATH = old

    def test_skips_invalid_lines(self, suggester, tmp_path):
        p = tmp_path / "unmatched.jsonl"
        p.write_text('{"text": "ok"}\nnot json\n{"text": "fine"}\n', encoding="utf-8")
        import src.modules.messages.rule_suggester as mod

        old = mod.UNMATCHED_PATH
        mod.UNMATCHED_PATH = p
        try:
            result = suggester.load_unmatched_messages()
            assert len(result) == 2
        finally:
            mod.UNMATCHED_PATH = old

    def test_limit(self, suggester, tmp_path):
        p = tmp_path / "unmatched.jsonl"
        lines = "\n".join(f'{{"text": "msg{i}"}}' for i in range(100))
        p.write_text(lines, encoding="utf-8")
        import src.modules.messages.rule_suggester as mod

        old = mod.UNMATCHED_PATH
        mod.UNMATCHED_PATH = p
        try:
            result = suggester.load_unmatched_messages(limit=5)
            assert len(result) == 5
        finally:
            mod.UNMATCHED_PATH = old

    def test_skips_empty_lines(self, suggester, tmp_path):
        p = tmp_path / "unmatched.jsonl"
        p.write_text('{"text": "a"}\n\n\n{"text": "b"}\n', encoding="utf-8")
        import src.modules.messages.rule_suggester as mod

        old = mod.UNMATCHED_PATH
        mod.UNMATCHED_PATH = p
        try:
            result = suggester.load_unmatched_messages()
            assert len(result) == 2
        finally:
            mod.UNMATCHED_PATH = old


class TestSimpleCluster:
    def test_groups_by_first_word(self, suggester):
        messages = [
            {"text": "快递多久到"},
            {"text": "快递多少钱"},
            {"text": "发货了吗"},
        ]
        clusters = suggester._simple_cluster(messages)
        # Chinese text without spaces -> first "word" is the entire string[:60]
        # But "快递多久到" and "快递多少钱" share prefix "快递" only if split by char
        # _simple_cluster splits by whitespace, so Chinese sentences are one token each
        assert len(clusters) == 3  # Each is its own cluster

    def test_limits_cluster_size(self, suggester):
        messages = [{"text": f"快递 问题{i}"} for i in range(10)]
        clusters = suggester._simple_cluster(messages)
        for c in clusters:
            assert len(c) <= 5

    def test_empty_input(self, suggester):
        assert suggester._simple_cluster([]) == []

    def test_uses_message_text_key(self, suggester):
        messages = [{"message_text": "运费多少"}]
        clusters = suggester._simple_cluster(messages)
        assert len(clusters) == 1


class TestSuggestions:
    def test_get_empty(self, suggester, tmp_path):
        result = suggester.get_suggestions()
        assert result == []

    def test_save_and_get(self, suggester, tmp_path):
        suggestions = [{"name": "test_rule", "keywords": ["测试"]}]
        suggester.save_suggestions(suggestions)
        result = suggester.get_suggestions()
        assert len(result) == 1
        assert result[0]["name"] == "test_rule"

    def test_get_non_list_returns_empty(self, suggester, tmp_path):
        import src.modules.messages.rule_suggester as mod

        old = mod.SYSTEM_CONFIG_PATH
        p = tmp_path / "system_config.json"
        p.write_text(json.dumps({"rule_suggestions": "not a list"}), encoding="utf-8")
        mod.SYSTEM_CONFIG_PATH = p
        try:
            result = suggester.get_suggestions()
            assert result == []
        finally:
            mod.SYSTEM_CONFIG_PATH = old


class TestAnalyzeAndSuggest:
    def test_too_few_messages(self, suggester, tmp_path):
        import src.modules.messages.rule_suggester as mod

        old = mod.UNMATCHED_PATH
        p = tmp_path / "unmatched.jsonl"
        p.write_text('{"text": "a"}\n{"text": "b"}\n', encoding="utf-8")
        mod.UNMATCHED_PATH = p
        try:
            result = suggester.analyze_and_suggest(min_messages=5)
            assert result == []
        finally:
            mod.UNMATCHED_PATH = old

    def test_with_mocked_ai(self, suggester, tmp_path):
        import src.modules.messages.rule_suggester as mod

        old_path = mod.UNMATCHED_PATH
        p = tmp_path / "unmatched.jsonl"
        lines = "\n".join(f'{{"text": "快递怎么寄{i}"}}' for i in range(10))
        p.write_text(lines, encoding="utf-8")
        mod.UNMATCHED_PATH = p

        mock_svc = MagicMock()
        mock_svc.client = True
        mock_svc._call_ai.return_value = (
            '[{"name":"test","keywords":["快递"],"reply":"请联系","priority":20,"categories":[],"phase":""}]'
        )

        try:
            with patch("src.modules.content.service.ContentService", return_value=mock_svc):
                with patch("src.modules.messages.rule_suggester.SYSTEM_CONFIG_PATH", tmp_path / "cfg.json"):
                    result = suggester.analyze_and_suggest(min_messages=3)
                    assert len(result) > 0
                    assert result[0]["name"] == "test"
                    assert "_source_cluster_size" in result[0]
        finally:
            mod.UNMATCHED_PATH = old_path


class TestAdoptSuggestion:
    def test_not_found(self, suggester):
        with patch.object(suggester, "get_suggestions", return_value=[]):
            assert not suggester.adopt_suggestion("nonexistent")

    def test_adopts_rule(self, suggester, tmp_path):
        suggestions = [{"name": "r1", "keywords": ["测试"], "_created_at": 123}]
        mock_cfg = {"auto_reply": {"custom_intent_rules": []}}

        with patch.object(suggester, "get_suggestions", return_value=suggestions):
            with patch("src.dashboard.config_service.read_system_config", return_value=mock_cfg):
                with patch("src.dashboard.config_service.write_system_config"):
                    with patch("src.modules.messages.rule_suggester.get_config"):
                        with patch.object(suggester, "save_suggestions"):
                            result = suggester.adopt_suggestion("r1")
                            assert result is True


class TestRejectSuggestion:
    def test_removes_suggestion(self, suggester):
        suggestions = [{"name": "r1"}, {"name": "r2"}]
        with patch.object(suggester, "get_suggestions", return_value=suggestions):
            with patch.object(suggester, "save_suggestions") as mock_save:
                result = suggester.reject_suggestion("r1")
                assert result is True
                mock_save.assert_called_once()
                remaining = mock_save.call_args[0][0]
                assert len(remaining) == 1
                assert remaining[0]["name"] == "r2"


class TestLoadWriteSystemConfig:
    def test_load_no_file(self, suggester, tmp_path):
        import src.modules.messages.rule_suggester as mod

        old = mod.SYSTEM_CONFIG_PATH
        mod.SYSTEM_CONFIG_PATH = tmp_path / "nonexistent.json"
        try:
            result = suggester._load_system_config()
            assert result == {}
        finally:
            mod.SYSTEM_CONFIG_PATH = old

    def test_load_and_write(self, suggester, tmp_path):
        import src.modules.messages.rule_suggester as mod

        old = mod.SYSTEM_CONFIG_PATH
        p = tmp_path / "cfg.json"
        mod.SYSTEM_CONFIG_PATH = p
        try:
            suggester._write_system_config({"key": "value"})
            result = suggester._load_system_config()
            assert result == {"key": "value"}
        finally:
            mod.SYSTEM_CONFIG_PATH = old

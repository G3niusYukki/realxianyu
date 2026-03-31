"""更新配置常量测试。"""

import os
from unittest.mock import patch


class TestUpdateConfig:
    def test_default_owner(self):
        import importlib
        import src.core.update_config as mod

        importlib.reload(mod)
        assert mod.GITHUB_OWNER == "G3niusYukki"

    def test_default_repo(self):
        import importlib
        import src.core.update_config as mod

        importlib.reload(mod)
        assert mod.GITHUB_REPO == "realxianyu"

    def test_default_token_empty(self):
        import importlib
        import src.core.update_config as mod

        importlib.reload(mod)
        assert mod.GITHUB_TOKEN == ""

    def test_asset_suffix(self):
        import importlib
        import src.core.update_config as mod

        importlib.reload(mod)
        assert mod.UPDATE_ASSET_SUFFIX == "-update.tar.gz"

    def test_env_override(self):
        with patch.dict(
            os.environ,
            {"GITHUB_UPDATE_OWNER": "test_owner", "GITHUB_UPDATE_REPO": "test_repo", "GITHUB_UPDATE_TOKEN": "tok123"},
        ):
            import importlib
            import src.core.update_config as mod

            importlib.reload(mod)
            assert mod.GITHUB_OWNER == "test_owner"
            assert mod.GITHUB_REPO == "test_repo"
            assert mod.GITHUB_TOKEN == "tok123"

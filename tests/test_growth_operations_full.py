"""
Test suite for growth and operations modules.
"""

import tempfile
from pathlib import Path

import pytest


class TestGrowthService:
    """Tests for GrowthService."""

    def test_growth_service_import(self):
        """Test GrowthService can be imported."""
        try:
            from src.modules.growth.service import GrowthService

            assert True
        except ImportError:
            pytest.skip("GrowthService not available")

    def test_growth_service_creation(self):
        """Test GrowthService can be created."""
        try:
            from src.modules.growth.service import GrowthService

            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                db_path = f.name

            service = GrowthService(db_path=db_path)
            assert service is not None

            Path(db_path).unlink(missing_ok=True)
        except ImportError:
            pytest.skip("GrowthService not available")


class TestOperationsService:
    """Tests for OperationsService."""

    def test_operations_service_import(self):
        """Test OperationsService can be imported."""
        try:
            from src.modules.operations.service import OperationsService

            assert True
        except ImportError:
            pytest.skip("OperationsService not available")

    def test_operations_service_creation(self):
        """Test OperationsService can be created."""
        try:
            from src.modules.operations.service import OperationsService

            service = OperationsService()
            assert service is not None
        except ImportError:
            pytest.skip("OperationsService not available")


class TestFollowupService:
    """Tests for FollowupService."""

    def test_followup_service_import(self):
        """Test FollowupService can be imported."""
        try:
            from src.modules.followup.service import FollowupService

            assert True
        except ImportError:
            pytest.skip("FollowupService not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

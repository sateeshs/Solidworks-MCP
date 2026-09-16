"""Tests for solidworks_mcp.automation.patterns — component pattern operations.

Tests verify input validation and argument calculation logic.
COM calls are mocked since we run on Linux.
"""

import math
from unittest.mock import MagicMock

import pytest

from solidworks_mcp.automation.patterns import PatternOperations
from solidworks_mcp.constants import SwErrors


class FakeAutomation(PatternOperations):
    """Minimal fake mixing in PatternOperations with mock dependencies."""

    def __init__(self, *, connected: bool = True, doc: MagicMock | None = None):
        self._connected = connected
        self._doc = doc or MagicMock()
        self._units = MagicMock()
        self._units.to_meters = lambda val: val / 1000.0

    @property
    def is_connected(self):
        return self._connected

    def connect(self):
        return {"success": True}

    def get_active_doc(self):
        if not self._connected:
            return None, {"success": False, "message": "Not connected"}
        return self._doc, None

    def _result(self, success, message, error_code=SwErrors.swSuccess, data=None):
        result = {"success": success, "message": message, "error_code": int(error_code)}
        if data:
            result["data"] = data
        return result


class TestLinearPatternValidation:
    """Input validation for linear patterns."""

    def test_rejects_empty_components(self):
        sw = FakeAutomation()
        result = sw.create_linear_pattern(components=[], count=3, spacing=50)
        assert result["success"] is False
        assert "No components" in result["message"]

    def test_rejects_count_less_than_two(self):
        sw = FakeAutomation()
        result = sw.create_linear_pattern(components=["part-1"], count=1, spacing=50)
        assert result["success"] is False
        assert "count" in result["message"].lower()

    def test_returns_error_when_not_connected(self):
        sw = FakeAutomation(connected=False)
        result = sw.create_linear_pattern(components=["part-1"], count=3, spacing=50)
        assert result["success"] is False


class TestLinearPatternSuccess:
    """Successful linear pattern creation."""

    def test_calls_feature_manager(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = True
        doc.FeatureManager.FeatureLinearPattern4.return_value = MagicMock()

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["channel-1"],
            count=3,
            spacing=100.0,
        )

        assert result["success"] is True
        assert result["data"]["count_d1"] == 3
        assert result["data"]["total"] == 3  # 3 x 1
        doc.FeatureManager.FeatureLinearPattern4.assert_called_once()

    def test_two_direction_pattern(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = True
        doc.FeatureManager.FeatureLinearPattern4.return_value = MagicMock()

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["part-1"],
            count=3,
            spacing=50.0,
            count2=2,
            spacing2=80.0,
        )

        assert result["success"] is True
        assert result["data"]["total"] == 6  # 3 x 2

    def test_handles_selection_failure(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = False

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["nonexistent-part"],
            count=3,
            spacing=50.0,
        )

        assert result["success"] is False
        assert "select" in result["message"].lower()

    def test_handles_pattern_failure(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = True
        doc.FeatureManager.FeatureLinearPattern4.return_value = None

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["part-1"],
            count=3,
            spacing=50.0,
        )

        assert result["success"] is False


class TestCircularPatternValidation:
    """Input validation for circular patterns."""

    def test_rejects_empty_components(self):
        sw = FakeAutomation()
        result = sw.create_circular_pattern(components=[], count=4)
        assert result["success"] is False

    def test_rejects_count_less_than_two(self):
        sw = FakeAutomation()
        result = sw.create_circular_pattern(components=["part-1"], count=1)
        assert result["success"] is False


class TestCircularPatternSuccess:
    """Successful circular pattern creation."""

    def test_equal_spacing_uses_360(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = True
        doc.FeatureManager.FeatureCircularPattern4.return_value = MagicMock()

        sw = FakeAutomation(doc=doc)
        result = sw.create_circular_pattern(
            components=["wheel-1"],
            count=4,
            equal_spacing=True,
        )

        assert result["success"] is True
        assert result["data"]["count"] == 4
        assert result["data"]["total_angle_deg"] == pytest.approx(360.0)
        assert result["data"]["angle_per_instance_deg"] == pytest.approx(90.0)

    def test_custom_angle(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = True
        doc.FeatureManager.FeatureCircularPattern4.return_value = MagicMock()

        sw = FakeAutomation(doc=doc)
        result = sw.create_circular_pattern(
            components=["bracket-1"],
            count=3,
            angle=180.0,
            equal_spacing=False,
        )

        assert result["success"] is True
        assert result["data"]["total_angle_deg"] == pytest.approx(180.0)
        assert result["data"]["angle_per_instance_deg"] == pytest.approx(60.0)

    def test_handles_pattern_failure(self):
        doc = MagicMock()
        doc.Extension.SelectByID2.return_value = True
        doc.FeatureManager.FeatureCircularPattern4.return_value = None

        sw = FakeAutomation(doc=doc)
        result = sw.create_circular_pattern(
            components=["part-1"],
            count=4,
        )

        assert result["success"] is False

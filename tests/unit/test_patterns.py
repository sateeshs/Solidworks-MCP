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


def _pattern_doc(*, feature=True, component_found=True):
    """Mock assembly doc with three default reference planes."""
    doc = MagicMock()
    planes = []
    for name in ("Front Plane", "Top Plane", "Right Plane"):
        plane = MagicMock()
        plane.Name = name
        plane.GetTypeName2 = "RefPlane"
        plane.Select2.return_value = True
        planes.append(plane)
    doc.FeatureManager.GetFeatures.return_value = planes
    doc.FeatureManager.CreateFeature.return_value = MagicMock() if feature else None
    doc.FeatureByName.return_value = MagicMock()  # reuse existing "MCP Axis" feature
    if component_found:
        doc.GetComponentByName.return_value.Select4.return_value = True
    else:
        doc.GetComponentByName.return_value = None
    return doc, planes


class TestLinearPatternSuccess:
    """Successful linear pattern creation."""

    def test_creates_local_linear_pattern(self):
        doc, planes = _pattern_doc()

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["channel-1"],
            count=3,
            spacing=100.0,
        )

        assert result["success"] is True
        assert result["data"]["count_d1"] == 3
        assert result["data"]["total"] == 3  # 3 x 1
        doc.FeatureManager.CreateDefinition.assert_called_once_with(108)
        doc.FeatureManager.CreateFeature.assert_called_once()
        data = doc.FeatureManager.CreateDefinition.return_value
        assert data.D1TotalInstances == 3
        assert data.D1Spacing == pytest.approx(0.1)
        assert data.D1ReverseDirection is False
        # +X direction -> Right Plane (normal X) selected with mark 2
        planes[2].Select2.assert_called_once_with(False, 2)

    def test_negative_direction_reverses(self):
        doc, planes = _pattern_doc()

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["part-1"], direction_x=0, direction_y=-1, count=2, spacing=25.0,
        )

        assert result["success"] is True
        planes[1].Select2.assert_called_once_with(False, 2)  # Top Plane (normal Y)
        assert doc.FeatureManager.CreateDefinition.return_value.D1ReverseDirection is True

    def test_two_direction_pattern(self):
        doc, planes = _pattern_doc()

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
        planes[1].Select2.assert_called_once_with(True, 4)  # 2nd dir Y, mark 4
        assert doc.FeatureManager.CreateDefinition.return_value.D2TotalInstances == 2

    def test_rejects_non_axis_aligned_direction(self):
        doc, _ = _pattern_doc()

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["part-1"], direction_x=1, direction_y=1, count=2,
        )

        assert result["success"] is False
        assert "axis-aligned" in result["message"]
        doc.FeatureManager.CreateFeature.assert_not_called()

    def test_handles_selection_failure(self):
        doc, _ = _pattern_doc(component_found=False)

        sw = FakeAutomation(doc=doc)
        result = sw.create_linear_pattern(
            components=["nonexistent-part"],
            count=3,
            spacing=50.0,
        )

        assert result["success"] is False
        assert "select" in result["message"].lower()

    def test_handles_pattern_failure(self):
        doc, _ = _pattern_doc(feature=False)

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
        doc, _ = _pattern_doc()

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
        doc.FeatureManager.CreateDefinition.assert_called_once_with(109)
        data = doc.FeatureManager.CreateDefinition.return_value
        assert data.EqualSpacing is True
        assert data.Spacing == pytest.approx(2 * math.pi)

    def test_custom_angle(self):
        doc, _ = _pattern_doc()

        sw = FakeAutomation(doc=doc)
        result = sw.create_circular_pattern(
            components=["bracket-1"],
            count=3,
            angle=180.0,
            equal_spacing=False,
        )

        assert result["success"] is True
        assert result["data"]["total_angle_deg"] == pytest.approx(180.0)
        # Partial arc includes both ends: 0, 90, 180
        assert result["data"]["angle_per_instance_deg"] == pytest.approx(90.0)
        data = doc.FeatureManager.CreateDefinition.return_value
        assert data.EqualSpacing is False
        assert data.Spacing == pytest.approx(math.pi / 2)

    def test_rejects_non_axis_aligned_axis(self):
        doc, _ = _pattern_doc()

        sw = FakeAutomation(doc=doc)
        result = sw.create_circular_pattern(
            components=["part-1"], axis_x=1, axis_y=1, count=4,
        )

        assert result["success"] is False
        assert "axis-aligned" in result["message"]

    def test_handles_pattern_failure(self):
        doc, _ = _pattern_doc(feature=False)

        sw = FakeAutomation(doc=doc)
        result = sw.create_circular_pattern(
            components=["part-1"],
            count=4,
        )

        assert result["success"] is False

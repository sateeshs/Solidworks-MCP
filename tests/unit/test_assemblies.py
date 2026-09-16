"""Tests for solidworks_mcp.automation.assemblies — assembly operations.

All SolidWorks COM calls are mocked. These tests verify logic flow,
argument conversion, and error handling without a Windows machine.
"""

from unittest.mock import MagicMock, PropertyMock

import pytest

from solidworks_mcp.automation.assemblies import (
    AssemblyOperations,
    _resolve_mate_type,
    _get_component_name,
    _extract_component_info,
    _extract_mate_info,
)
from solidworks_mcp.constants import SwErrors, SwMateTypes


# ============================================================================
# Helper function tests (no COM needed)
# ============================================================================


class TestResolveMateType:
    """Test mate type resolution from string/int."""

    def test_string_coincident(self):
        assert _resolve_mate_type("coincident") == SwMateTypes.swMateCOINCIDENT

    def test_string_concentric(self):
        assert _resolve_mate_type("concentric") == SwMateTypes.swMateCONCENTRIC

    def test_string_distance(self):
        assert _resolve_mate_type("distance") == SwMateTypes.swMateDISTANCE

    def test_string_case_insensitive(self):
        assert _resolve_mate_type("COINCIDENT") == SwMateTypes.swMateCOINCIDENT

    def test_string_lock(self):
        assert _resolve_mate_type("lock") == SwMateTypes.swMateLOCK

    def test_int_valid(self):
        assert _resolve_mate_type(0) == 0  # swMateCOINCIDENT

    def test_int_valid_distance(self):
        assert _resolve_mate_type(5) == 5  # swMateDISTANCE

    def test_int_invalid(self):
        assert _resolve_mate_type(999) is None

    def test_string_invalid(self):
        assert _resolve_mate_type("bogus") is None

    def test_none_returns_none(self):
        assert _resolve_mate_type(None) is None

    def test_all_string_types(self):
        expected = {
            "coincident": 0,
            "concentric": 1,
            "perpendicular": 2,
            "parallel": 3,
            "tangent": 4,
            "distance": 5,
            "angle": 6,
            "lock": 16,
            "width": 18,
        }
        for name, value in expected.items():
            assert _resolve_mate_type(name) == value


class TestGetComponentName:
    """Test safe component name extraction."""

    def test_name2_property(self):
        comp = MagicMock()
        comp.Name2 = "channel-1"
        assert _get_component_name(comp) == "channel-1"

    def test_name2_method(self):
        comp = MagicMock()
        comp.Name2 = MagicMock(return_value="channel-2")
        assert _get_component_name(comp) == "channel-2"

    def test_falls_back_to_name(self):
        comp = MagicMock(spec=[])
        comp.Name = "fallback-name"
        assert _get_component_name(comp) == "fallback-name"

    def test_returns_unknown_on_total_failure(self):
        comp = MagicMock(spec=[])
        assert _get_component_name(comp) == "unknown"


class TestExtractComponentInfo:
    """Test component info extraction from mock COM objects."""

    def test_extracts_basic_info(self):
        comp = MagicMock()
        comp.Name2 = "wheel-1"
        comp.IsSuppressed.return_value = False
        comp.Visible = True
        comp.GetPathName.return_value = "C:\\goBILDA\\wheel.step"

        info = _extract_component_info(comp)

        assert info["name"] == "wheel-1"
        assert info["suppressed"] is False
        assert info["visible"] is True
        assert info["path"] == "C:\\goBILDA\\wheel.step"

    def test_handles_suppressed(self):
        comp = MagicMock()
        comp.Name2 = "hidden-part"
        comp.IsSuppressed.return_value = True
        comp.Visible = False
        comp.GetPathName.return_value = ""

        info = _extract_component_info(comp)

        assert info["suppressed"] is True
        assert info["visible"] is False


class TestExtractMateInfo:
    """Test mate info extraction."""

    def test_extracts_name_and_type(self):
        feat = MagicMock()
        feat.Name = "Coincident1"
        feat.GetTypeName2 = "MateCoincident"

        info = _extract_mate_info(feat)

        assert info is not None
        assert info["name"] == "Coincident1"
        assert info["type"] == "MateCoincident"

    def test_returns_none_on_error(self):
        feat = MagicMock()
        type(feat).Name = PropertyMock(side_effect=Exception("COM error"))

        assert _extract_mate_info(feat) is None

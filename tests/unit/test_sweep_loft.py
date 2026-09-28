"""Tests for sweep/loft and create_plane in solidworks_mcp.automation.features.

COM calls are mocked. These pin the live-verified API signatures (argument
counts, selection marks, reference-plane constraint) so they don't regress.
"""

from unittest.mock import MagicMock

import pytest

from solidworks_mcp.automation.features import FeatureOperations
from solidworks_mcp.constants import SwErrors


class FakeAutomation(FeatureOperations):
    """Minimal fake mixing in FeatureOperations with mock dependencies."""

    def __init__(self, doc: MagicMock | None = None):
        self._doc = doc or MagicMock()
        self._units = MagicMock()
        self._units.to_meters = lambda val, unit=None: val / 1000.0
        self._units.default_unit.value = "mm"

    def get_active_doc(self):
        return self._doc, None

    def _result(self, success, message, error_code=SwErrors.swSuccess, data=None):
        result = {"success": success, "message": message, "error_code": int(error_code)}
        if data:
            result["data"] = data
        return result


def _doc(select_ok=True):
    doc = MagicMock()
    doc.SketchManager.ActiveSketch = None
    # An empty feature tree. Without this, FirstFeature auto-creates a mock
    # whose GetNextFeature yields a fresh truthy child forever, so the
    # diagnostic tree walk on the failure path never terminates.
    doc.FirstFeature = None
    doc.Extension.SelectByID2.return_value = select_ok
    feat = MagicMock()
    feat.Name = "Feature1"
    fm = doc.FeatureManager
    for method in ("InsertProtrusionSwept4", "InsertCutSwept5",
                   "InsertProtrusionBlend2", "InsertCutBlend"):
        getattr(fm, method).return_value = feat
    return doc


def _marks(doc):
    """(name, append, mark) for each SelectByID2 call."""
    return [(c.args[0], c.args[5], c.args[6]) for c in doc.Extension.SelectByID2.call_args_list]


class TestSweep:
    def test_boss_sweep_selects_profile_mark1_path_mark4(self):
        doc = _doc()
        result = FakeAutomation(doc).sweep_sketch("Sketch1", "Sketch2")

        assert result["success"] is True
        assert result["data"]["feature"] == "Feature1"
        assert _marks(doc) == [("Sketch1", False, 1), ("Sketch2", True, 4)]
        args = doc.FeatureManager.InsertProtrusionSwept4.call_args.args
        assert len(args) == 20
        assert args[12] is True  # Merge
        doc.FeatureManager.InsertCutSwept5.assert_not_called()

    def test_cut_sweep_uses_22_arg_cut_api(self):
        doc = _doc()
        result = FakeAutomation(doc).sweep_sketch("Sketch3", "Sketch2", cut=True)

        assert result["success"] is True
        assert len(doc.FeatureManager.InsertCutSwept5.call_args.args) == 22
        doc.FeatureManager.InsertProtrusionSwept4.assert_not_called()

    def test_reports_missing_sketch(self):
        doc = _doc(select_ok=False)
        result = FakeAutomation(doc).sweep_sketch("Nope", "Sketch2")

        assert result["success"] is False
        assert "Nope" in result["message"]
        doc.FeatureManager.InsertProtrusionSwept4.assert_not_called()

    def test_reports_feature_failure(self):
        doc = _doc()
        doc.FeatureManager.InsertProtrusionSwept4.return_value = None
        result = FakeAutomation(doc).sweep_sketch("Sketch1", "Sketch2")

        assert result["success"] is False
        assert "closed" in result["message"]


class TestLoft:
    def test_boss_loft_selects_all_profiles_mark1(self):
        doc = _doc()
        result = FakeAutomation(doc).loft_sketches(["Sketch1", "Sketch2", "Sketch3"])

        assert result["success"] is True
        assert _marks(doc) == [
            ("Sketch1", False, 1), ("Sketch2", True, 1), ("Sketch3", True, 1)
        ]
        args = doc.FeatureManager.InsertProtrusionBlend2.call_args.args
        assert len(args) == 18
        assert args[0] is False  # Closed

    def test_closed_cut_loft_uses_12_arg_cut_api(self):
        doc = _doc()
        result = FakeAutomation(doc).loft_sketches(["Sketch1", "Sketch2"], cut=True, closed=True)

        assert result["success"] is True
        args = doc.FeatureManager.InsertCutBlend.call_args.args
        assert len(args) == 12
        assert args[0] is True  # Closed

    @pytest.mark.parametrize("names", [[], ["Sketch1"]])
    def test_needs_two_profiles(self, names):
        doc = _doc()
        result = FakeAutomation(doc).loft_sketches(names)

        assert result["success"] is False
        doc.Extension.SelectByID2.assert_not_called()


class TestCreatePlane:
    def test_positive_offset_uses_distance_constraint(self):
        doc = _doc()
        FakeAutomation(doc).create_plane(40, "Front")

        constraint, distance = doc.FeatureManager.InsertRefPlane.call_args.args[:2]
        assert constraint == 8  # Distance (not Parallel|Coincident, which ignores it)
        assert distance == pytest.approx(0.04)

    def test_negative_offset_flips(self):
        doc = _doc()
        FakeAutomation(doc).create_plane(-40, "Front")

        constraint, distance = doc.FeatureManager.InsertRefPlane.call_args.args[:2]
        assert constraint == 8 | 256
        assert distance == pytest.approx(0.04)
